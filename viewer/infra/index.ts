import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

// ---- config -----------------------------------------------------------------
const cfg = new pulumi.Config("viewer");
const namePrefix = cfg.get("namePrefix") ?? "ai-models-viewer";
const presignTtl = cfg.getNumber("presignTtl") ?? 900;
const authDisabled = cfg.getBoolean("authDisabled") ?? false;
const apiToken = cfg.getSecret("apiToken") ?? pulumi.secret(""); // set via `pulumi config set --secret`

const region = aws.getRegionOutput().name;
const accountId = aws.getCallerIdentityOutput().accountId;
const name = (s: string) => `${namePrefix}-${s}`;

// ---- data storage -----------------------------------------------------------
const dataBucket = new aws.s3.BucketV2(name("data"), {});
new aws.s3.BucketPublicAccessBlock(name("data-pab"), {
  bucket: dataBucket.id,
  blockPublicAcls: true,
  blockPublicPolicy: true,
  ignorePublicAcls: true,
  restrictPublicBuckets: true,
});
// CORS so the SPA can GET .3mf files via presigned URLs from the browser.
new aws.s3.BucketCorsConfigurationV2(name("data-cors"), {
  bucket: dataBucket.id,
  corsRules: [{
    allowedMethods: ["GET", "HEAD"],
    allowedOrigins: ["*"],
    allowedHeaders: ["*"],
    maxAgeSeconds: 3000,
  }],
});

const table = new aws.dynamodb.Table(name("index"), {
  billingMode: "PAY_PER_REQUEST",
  hashKey: "pk",
  rangeKey: "sk",
  attributes: [
    { name: "pk", type: "S" },
    { name: "sk", type: "S" },
  ],
});

// ---- WebSocket API (created before the role so the policy can scope to it) ---
const wsApi = new aws.apigatewayv2.Api(name("ws"), {
  protocolType: "WEBSOCKET",
  routeSelectionExpression: "$request.body.action",
});
const stageName = "prod";

// ---- lambda IAM role --------------------------------------------------------
const role = new aws.iam.Role(name("lambda-role"), {
  assumeRolePolicy: JSON.stringify({
    Version: "2012-10-17",
    Statement: [{ Effect: "Allow", Principal: { Service: "lambda.amazonaws.com" }, Action: "sts:AssumeRole" }],
  }),
});
new aws.iam.RolePolicyAttachment(name("lambda-logs"), {
  role: role.name,
  policyArn: "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
});
new aws.iam.RolePolicy(name("lambda-policy"), {
  role: role.id,
  policy: pulumi.all([table.arn, dataBucket.arn, wsApi.executionArn]).apply(([tableArn, bucketArn, apiArn]) =>
    JSON.stringify({
      Version: "2012-10-17",
      Statement: [
        {
          Effect: "Allow",
          Action: ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:Query", "dynamodb:BatchWriteItem"],
          Resource: [tableArn, `${tableArn}/index/*`],
        },
        {
          Effect: "Allow",
          Action: ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
          Resource: `${bucketArn}/*`,
        },
        { Effect: "Allow", Action: ["s3:ListBucket"], Resource: bucketArn },
        { Effect: "Allow", Action: ["execute-api:ManageConnections"], Resource: `${apiArn}/*` },
      ],
    })),
});

// ---- lambda code (both functions share one archive; different handlers) ------
const code = new pulumi.asset.FileArchive("../backend/src");
const wsEndpoint = pulumi.interpolate`https://${wsApi.id}.execute-api.${region}.amazonaws.com/${stageName}`;

const directoryFn = new aws.lambda.Function(name("directory"), {
  runtime: "python3.12",
  handler: "directory.handler.handler",
  role: role.arn,
  code,
  timeout: 30,
  memorySize: 256,
  environment: {
    variables: {
      TABLE_NAME: table.name,
      BUCKET_NAME: dataBucket.bucket,
      API_TOKEN: apiToken,
      AUTH_DISABLED: authDisabled ? "true" : "false",
      PRESIGN_TTL: String(presignTtl),
    },
  },
});

const indexerFn = new aws.lambda.Function(name("indexer"), {
  runtime: "python3.12",
  handler: "indexer.handler.handler",
  role: role.arn,
  code,
  timeout: 30,
  memorySize: 256,
  environment: {
    variables: {
      TABLE_NAME: table.name,
      BUCKET_NAME: dataBucket.bucket,
      WS_ENDPOINT: wsEndpoint,
    },
  },
});

// ---- wire the WebSocket API to the directory lambda -------------------------
const integration = new aws.apigatewayv2.Integration(name("ws-integ"), {
  apiId: wsApi.id,
  integrationType: "AWS_PROXY",
  integrationUri: directoryFn.invokeArn,
});
const routeTarget = pulumi.interpolate`integrations/${integration.id}`;
for (const rk of ["$connect", "$disconnect", "$default"]) {
  new aws.apigatewayv2.Route(name(`ws-route-${rk.replace("$", "")}`), {
    apiId: wsApi.id,
    routeKey: rk,
    target: routeTarget,
  });
}
new aws.lambda.Permission(name("ws-perm"), {
  action: "lambda:InvokeFunction",
  function: directoryFn.name,
  principal: "apigateway.amazonaws.com",
  sourceArn: pulumi.interpolate`${wsApi.executionArn}/*/*`,
});
const wsStage = new aws.apigatewayv2.Stage(name("ws-stage"), {
  apiId: wsApi.id,
  name: stageName,
  autoDeploy: true,
});

// ---- S3 -> indexer notification --------------------------------------------
new aws.lambda.Permission(name("s3-perm"), {
  action: "lambda:InvokeFunction",
  function: indexerFn.name,
  principal: "s3.amazonaws.com",
  sourceArn: dataBucket.arn,
});
new aws.s3.BucketNotification(name("data-notify"), {
  bucket: dataBucket.id,
  lambdaFunctions: [{
    lambdaFunctionArn: indexerFn.arn,
    events: ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"],
    filterSuffix: ".3mf",
  }],
});

// ---- frontend hosting: private S3 + CloudFront (OAC) ------------------------
const siteBucket = new aws.s3.BucketV2(name("site"), {});
new aws.s3.BucketPublicAccessBlock(name("site-pab"), {
  bucket: siteBucket.id,
  blockPublicAcls: true,
  blockPublicPolicy: true,
  ignorePublicAcls: true,
  restrictPublicBuckets: true,
});
const oac = new aws.cloudfront.OriginAccessControl(name("oac"), {
  originAccessControlOriginType: "s3",
  signingBehavior: "always",
  signingProtocol: "sigv4",
});
const cdn = new aws.cloudfront.Distribution(name("cdn"), {
  enabled: true,
  defaultRootObject: "index.html",
  origins: [{
    originId: "site",
    domainName: siteBucket.bucketRegionalDomainName,
    originAccessControlId: oac.id,
  }],
  defaultCacheBehavior: {
    targetOriginId: "site",
    viewerProtocolPolicy: "redirect-to-https",
    allowedMethods: ["GET", "HEAD", "OPTIONS"],
    cachedMethods: ["GET", "HEAD"],
    cachePolicyId: "658327ea-f89d-4fab-a63d-7e88639e58f6", // managed CachingOptimized
  },
  // SPA routing: serve index.html for client-side routes / missing keys.
  customErrorResponses: [
    { errorCode: 403, responseCode: 200, responsePagePath: "/index.html" },
    { errorCode: 404, responseCode: 200, responsePagePath: "/index.html" },
  ],
  restrictions: { geoRestriction: { restrictionType: "none" } },
  viewerCertificate: { cloudfrontDefaultCertificate: true },
});
// Let this CloudFront distribution read the private site bucket.
new aws.s3.BucketPolicy(name("site-policy"), {
  bucket: siteBucket.id,
  policy: pulumi.all([siteBucket.arn, cdn.arn]).apply(([bucketArn, cdnArn]) =>
    JSON.stringify({
      Version: "2012-10-17",
      Statement: [{
        Effect: "Allow",
        Principal: { Service: "cloudfront.amazonaws.com" },
        Action: "s3:GetObject",
        Resource: `${bucketArn}/*`,
        Condition: { StringEquals: { "AWS:SourceArn": cdnArn } },
      }],
    })),
});

// ---- outputs (consumed by the Makefile deploy step + the frontend) ---------
export const dataBucketName = dataBucket.bucket;
export const tableName = table.name;
export const wsUrl = pulumi.interpolate`wss://${wsApi.id}.execute-api.${region}.amazonaws.com/${stageName}`;
export const siteBucketName = siteBucket.bucket;
export const cloudfrontUrl = pulumi.interpolate`https://${cdn.domainName}`;
export const cloudfrontDistributionId = cdn.id;
