# Roof analysis — span 8500 mm, pitch 27°, 35x105 F7 Oregon, trusses @ 1200 c/c

Geometry: rise 2165 mm, rafter 4770 on slope (wall→collar 2567, collar→apex 2203), collar 3925 long at 1165 above the plate; 10 trusses modelled over 3 x 4000 mm bays, results for truss at y=5400.

### as built: purlins + 40x190 ridge on cross walls @ 4 m, joists on mid wall + hanging beams — 35x105 F7, ridge (40, 190), span 8500, pitch 27°, trusses @ 1200 c/c, cross walls @ 4000

Governing utilisation per member (ULS, demand/capacity; >1.0 = FAIL):

| group | combo | tag | util | M* kNm | Md kNm | N* kN | Ncx kN | Ncy kN | Nt kN | k12b | k12cy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| collar | 1.2G+1.5Q | collar tie | 8.69 | 0.05 | 0.39 | -3.71 | 3.84 | 0.43 | 26.60 | 0.51 | 0.01 |
| purlin | 1.2G+Wa | under-purlin L | 4.20 | -1.98 | 0.47 | 0.00 | 5.90 | 7.28 | 28.30 | 0.58 | 0.22 |
| rafter | 1.2G+1.5Qp | rafter L lower | 1.73 | 1.11 | 0.79 | -2.66 | 9.27 | 8.38 | 27.45 | 1.00 | 0.26 |
| tie | 1.2G+1.5Qc | ceiling joist | 1.08 | 0.63 | 0.61 | 1.20 | 13.53 | 26.09 | 27.45 | 0.77 | 0.80 |
| ridge | 1.2G+1.5Q | ridge beam | 0.87 | -0.89 | 1.03 | 0.00 | 25.05 | 12.34 | 55.01 | 0.36 | 0.19 |

Support reactions (kN; H = horizontal thrust):

| support | |H| max | V max (down) | V min (uplift if <0) |
|---|---|---|---|
| joist prop 1 (mid truss) | 0.00 | 1.17 | 0.36 |
| joist prop 2 (mid truss) | 0.00 | 0.44 | 0.22 |
| joist prop 3 (mid truss) | 0.00 | 0.54 | 0.36 |
| purlin on cross wall (L y=0) | 0.00 | 1.67 | -0.14 |
| purlin on cross wall (L y=12000) | 0.00 | 1.67 | -0.14 |
| purlin on cross wall (L y=4000) | 0.00 | 6.08 | -1.47 |
| purlin on cross wall (L y=8000) | 0.00 | 6.08 | -1.47 |
| purlin on cross wall (R y=0) | 0.00 | 0.20 | -1.60 |
| purlin on cross wall (R y=12000) | 0.00 | 0.20 | -1.60 |
| purlin on cross wall (R y=4000) | 0.00 | 1.92 | -5.50 |
| purlin on cross wall (R y=8000) | 0.00 | 1.92 | -5.50 |
| ridge on cross wall (y=0) | 0.00 | 0.77 | -0.53 |
| ridge on cross wall (y=12000) | 0.00 | 0.77 | -0.53 |
| ridge on cross wall (y=4000) | 0.00 | 3.30 | -2.17 |
| ridge on cross wall (y=8000) | 0.00 | 3.30 | -2.17 |
| wall L (mid truss) | 2.44 | 2.86 | -1.87 |
| wall R (mid truss) | 0.00 | 2.86 | -1.87 |

Serviceability deflections, mid-bay truss (mm; limits span/300: rafter 15.9, joist span 2125 → 7.1, purlin bay 4000 → 13.3):

| case | j2 | rafter_mm | lower_seg_mm | collar_node_mm | apex_mm | spread_mm | joist_sag_mm | purlin_mm |
|---|---|---|---|---|---|---|---|---|
| G long-term | 3 | -4.54 | -3.99 | -1.87 | -1.57 | 0.88 | -2.26 | -2.35 |
| 0.7Q short-term | 1 | -1.98 | -1.76 | -0.72 | -0.60 | 0.34 | 0.00 | -0.90 |
| Ws uplift | 1 | 4.68 | 4.24 | 1.42 | 1.10 | -0.60 | 0.00 | 1.76 |

Collar-tie lap: N* = 4.80 kN (compression, 1.2G+Wd) ≈ 15 x 3.15 mm nails each end (Q_k 0.515 kN J4, φ 0.80, k1 1.0, k17 0.8), or an M12 bolt.

![as built: purlins + 40x190 ridge on cross walls @ 4 m, joists on mid wall + hanging beams](asbuilt_35x105.png)

### what-if: joists on the mid wall only (no hanging beams) — 35x105 F7, ridge (40, 190), span 8500, pitch 27°, trusses @ 1200 c/c, cross walls @ 4000

Governing utilisation per member (ULS, demand/capacity; >1.0 = FAIL):

| group | combo | tag | util | M* kNm | Md kNm | N* kN | Ncx kN | Ncy kN | Nt kN | k12b | k12cy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| collar | 1.2G+1.5Q | collar tie | 8.69 | 0.05 | 0.39 | -3.71 | 3.84 | 0.43 | 26.60 | 0.51 | 0.01 |
| purlin | 1.2G+Wa | under-purlin L | 4.20 | -1.98 | 0.47 | 0.00 | 5.90 | 7.28 | 28.30 | 0.58 | 0.22 |
| tie | 1.2G+1.5Qc | ceiling joist | 3.78 | 1.39 | 0.37 | 1.20 | 3.38 | 26.09 | 27.45 | 0.47 | 0.80 |
| rafter | 1.2G+1.5Qp | rafter L lower | 1.73 | 1.11 | 0.79 | -2.66 | 9.27 | 8.38 | 27.45 | 1.00 | 0.26 |
| ridge | 1.2G+1.5Q | ridge beam | 0.87 | -0.89 | 1.03 | 0.00 | 25.05 | 12.34 | 55.01 | 0.36 | 0.19 |

Support reactions (kN; H = horizontal thrust):

| support | |H| max | V max (down) | V min (uplift if <0) |
|---|---|---|---|
| joist prop 1 (mid truss) | 0.00 | 1.97 | 0.78 |
| purlin on cross wall (L y=0) | 0.00 | 1.67 | -0.14 |
| purlin on cross wall (L y=12000) | 0.00 | 1.67 | -0.14 |
| purlin on cross wall (L y=4000) | 0.00 | 6.08 | -1.47 |
| purlin on cross wall (L y=8000) | 0.00 | 6.08 | -1.47 |
| purlin on cross wall (R y=0) | 0.00 | 0.20 | -1.60 |
| purlin on cross wall (R y=12000) | 0.00 | 0.20 | -1.60 |
| purlin on cross wall (R y=4000) | 0.00 | 1.92 | -5.50 |
| purlin on cross wall (R y=8000) | 0.00 | 1.92 | -5.50 |
| ridge on cross wall (y=0) | 0.00 | 0.77 | -0.53 |
| ridge on cross wall (y=12000) | 0.00 | 0.77 | -0.53 |
| ridge on cross wall (y=4000) | 0.00 | 3.30 | -2.17 |
| ridge on cross wall (y=8000) | 0.00 | 3.30 | -2.17 |
| wall L (mid truss) | 2.44 | 3.01 | -1.76 |
| wall R (mid truss) | 0.00 | 3.01 | -1.76 |

Serviceability deflections, mid-bay truss (mm; limits span/300: rafter 15.9, joist span 4250 → 14.2, purlin bay 4000 → 13.3):

| case | j2 | rafter_mm | lower_seg_mm | collar_node_mm | apex_mm | spread_mm | joist_sag_mm | purlin_mm |
|---|---|---|---|---|---|---|---|---|
| G long-term | 3 | -4.54 | -3.99 | -1.87 | -1.57 | 0.88 | -31.31 | -2.35 |
| 0.7Q short-term | 1 | -1.98 | -1.76 | -0.72 | -0.60 | 0.34 | 0.00 | -0.90 |
| Ws uplift | 1 | 4.68 | 4.24 | 1.42 | 1.10 | -0.60 | 0.00 | 1.76 |

Collar-tie lap: N* = 4.80 kN (compression, 1.2G+Wd) ≈ 15 x 3.15 mm nails each end (Q_k 0.515 kN J4, φ 0.80, k1 1.0, k17 0.8), or an M12 bolt.

![what-if: joists on the mid wall only (no hanging beams)](nobeams_35x105.png)

### what-if: no ridge beam — 35x105 F7, ridge none, span 8500, pitch 27°, trusses @ 1200 c/c, cross walls @ 4000

Governing utilisation per member (ULS, demand/capacity; >1.0 = FAIL):

| group | combo | tag | util | M* kNm | Md kNm | N* kN | Ncx kN | Ncy kN | Nt kN | k12b | k12cy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| collar | 1.2G+1.5Q | collar tie | 9.21 | 0.05 | 0.39 | -3.92 | 3.84 | 0.43 | 26.60 | 0.51 | 0.01 |
| purlin | 1.2G+Wa | under-purlin L | 4.25 | -2.00 | 0.47 | 0.00 | 5.90 | 7.28 | 28.30 | 0.58 | 0.22 |
| rafter | 1.2G+1.5Qp | rafter L lower | 1.78 | 1.11 | 0.79 | -3.07 | 9.27 | 8.38 | 27.45 | 1.00 | 0.26 |
| tie | 1.2G+1.5Qc | ceiling joist | 1.09 | 0.63 | 0.61 | 1.37 | 13.53 | 26.09 | 27.45 | 0.77 | 0.80 |

Support reactions (kN; H = horizontal thrust):

| support | |H| max | V max (down) | V min (uplift if <0) |
|---|---|---|---|
| joist prop 1 (mid truss) | 0.00 | 1.17 | 0.36 |
| joist prop 2 (mid truss) | 0.00 | 0.44 | 0.22 |
| joist prop 3 (mid truss) | 0.00 | 0.54 | 0.36 |
| purlin on cross wall (L y=0) | 0.00 | 1.69 | -0.19 |
| purlin on cross wall (L y=12000) | 0.00 | 1.69 | -0.19 |
| purlin on cross wall (L y=4000) | 0.00 | 6.28 | -1.85 |
| purlin on cross wall (L y=8000) | 0.00 | 6.28 | -1.85 |
| purlin on cross wall (R y=0) | 0.00 | 0.26 | -1.59 |
| purlin on cross wall (R y=12000) | 0.00 | 0.26 | -1.59 |
| purlin on cross wall (R y=4000) | 0.00 | 2.48 | -5.34 |
| purlin on cross wall (R y=8000) | 0.00 | 2.48 | -5.34 |
| wall L (mid truss) | 2.44 | 3.22 | -2.17 |
| wall R (mid truss) | 0.00 | 3.22 | -2.17 |

Serviceability deflections, mid-bay truss (mm; limits span/300: rafter 15.9, joist span 2125 → 7.1, purlin bay 4000 → 13.3):

| case | j2 | rafter_mm | lower_seg_mm | collar_node_mm | apex_mm | spread_mm | joist_sag_mm | purlin_mm |
|---|---|---|---|---|---|---|---|---|
| G long-term | 3 | -4.59 | -4.00 | -2.10 | -1.86 | 1.01 | -2.26 | -2.35 |
| 0.7Q short-term | 1 | -2.00 | -1.77 | -0.83 | -0.75 | 0.40 | 0.00 | -0.93 |
| Ws uplift | 1 | 4.73 | 4.26 | 1.63 | 1.38 | -0.72 | 0.00 | 1.83 |

Collar-tie lap: N* = 5.02 kN (compression, 1.2G+Wd) ≈ 16 x 3.15 mm nails each end (Q_k 0.515 kN J4, φ 0.80, k1 1.0, k17 0.8), or an M12 bolt.

![what-if: no ridge beam](noridge_35x105.png)

### what-if: purlins as bracing only (no cross walls) — 35x105 F7, ridge (40, 190), span 8500, pitch 27°, trusses @ 1200 c/c, cross walls @ 0

Governing utilisation per member (ULS, demand/capacity; >1.0 = FAIL):

| group | combo | tag | util | M* kNm | Md kNm | N* kN | Ncx kN | Ncy kN | Nt kN | k12b | k12cy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| collar | 1.2G+1.5Q | collar tie | 7.97 | 0.05 | 0.39 | -3.40 | 3.84 | 0.43 | 26.60 | 0.51 | 0.01 |
| rafter | 1.2G+Wa | rafter R lower | 2.68 | -1.61 | 0.62 | -1.09 | 14.32 | 12.95 | 28.30 | 0.76 | 0.39 |
| tie | 1.2G+1.5Qc | ceiling joist | 1.08 | 0.63 | 0.61 | 1.33 | 13.53 | 26.09 | 27.45 | 0.77 | 0.80 |

Support reactions (kN; H = horizontal thrust):

| support | |H| max | V max (down) | V min (uplift if <0) |
|---|---|---|---|
| joist prop 1 (mid truss) | 0.00 | 1.17 | 0.36 |
| joist prop 2 (mid truss) | 0.00 | 0.44 | 0.22 |
| joist prop 3 (mid truss) | 0.00 | 0.54 | 0.36 |
| wall L (mid truss) | 2.44 | 3.20 | -2.20 |
| wall R (mid truss) | 0.00 | 3.20 | -2.20 |

Serviceability deflections, mid-bay truss (mm; limits span/300: rafter 15.9, joist span 2125 → 7.1):

| case | j2 | rafter_mm | lower_seg_mm | collar_node_mm | apex_mm | spread_mm | joist_sag_mm | purlin_mm |
|---|---|---|---|---|---|---|---|---|
| G long-term | 3 | -4.56 | -3.99 | -2.02 | -1.80 | 0.97 | -2.26 | 0.00 |
| 0.7Q short-term | 1 | -2.00 | -1.77 | -0.84 | -0.75 | 0.40 | 0.00 | 0.00 |
| Ws uplift | 1 | 4.73 | 4.26 | 1.64 | 1.39 | -0.72 | 0.00 | 0.00 |

Collar-tie lap: N* = 4.44 kN (compression, 1.2G+Wd) ≈ 13 x 3.15 mm nails each end (Q_k 0.515 kN J4, φ 0.80, k1 1.0, k17 0.88), or an M12 bolt.

![what-if: purlins as bracing only (no cross walls)](nowalls_35x105.png)

### what-if: every collar node rigidly propped — 35x105 F7, ridge (40, 190), span 8500, pitch 27°, trusses @ 1200 c/c, cross walls @ 0

Governing utilisation per member (ULS, demand/capacity; >1.0 = FAIL):

| group | combo | tag | util | M* kNm | Md kNm | N* kN | Ncx kN | Ncy kN | Nt kN | k12b | k12cy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rafter | 1.2G+1.5Qp | rafter L lower | 1.35 | 1.03 | 0.79 | -0.39 | 9.27 | 8.38 | 27.45 | 1.00 | 0.26 |
| tie | 1.2G+1.5Qc | ceiling joist | 1.04 | 0.63 | 0.61 | 0.06 | 13.53 | 26.09 | 27.45 | 0.77 | 0.80 |
| collar | 1.35G | collar tie | 0.23 | 0.05 | 0.24 | 0.22 | 2.33 | 0.26 | 16.13 | 0.51 | 0.01 |

Support reactions (kN; H = horizontal thrust):

| support | |H| max | V max (down) | V min (uplift if <0) |
|---|---|---|---|
| joist prop 1 (mid truss) | 0.00 | 1.17 | 0.36 |
| joist prop 2 (mid truss) | 0.00 | 0.44 | 0.22 |
| joist prop 3 (mid truss) | 0.00 | 0.54 | 0.36 |
| strut L (mid truss) | 0.00 | 2.40 | -1.78 |
| strut R (mid truss) | 0.00 | 2.33 | -1.78 |
| wall L (mid truss) | 2.44 | 1.18 | -0.42 |
| wall R (mid truss) | 0.00 | 0.88 | -0.42 |

Serviceability deflections, mid-bay truss (mm; limits span/300: rafter 15.9, joist span 2125 → 7.1):

| case | j2 | rafter_mm | lower_seg_mm | collar_node_mm | apex_mm | spread_mm | joist_sag_mm | purlin_mm |
|---|---|---|---|---|---|---|---|---|
| G long-term | 3 | -3.67 | -3.73 | 0.00 | -0.19 | 0.04 | -2.26 | 0.00 |
| 0.7Q short-term | 1 | -1.64 | -1.66 | 0.00 | -0.09 | 0.02 | 0.00 | 0.00 |
| Ws uplift | 1 | 4.02 | 4.04 | 0.00 | 0.09 | 0.03 | 0.00 | 0.00 |

Collar-tie lap: N* = 0.77 kN (tension, 1.2G+Wa) ≈ 2 x 3.15 mm nails each end (Q_k 0.515 kN J4, φ 0.80, k1 1.0, k17 1.0), or an M12 bolt.

![what-if: every collar node rigidly propped](strutted_35x105.png)

### what-if: as built + collar braced at third points — 35x105 F7, ridge (40, 190), span 8500, pitch 27°, trusses @ 1200 c/c, cross walls @ 4000

Governing utilisation per member (ULS, demand/capacity; >1.0 = FAIL):

| group | combo | tag | util | M* kNm | Md kNm | N* kN | Ncx kN | Ncy kN | Nt kN | k12b | k12cy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| purlin | 1.2G+Wa | under-purlin L | 4.20 | -1.98 | 0.47 | 0.00 | 5.90 | 7.28 | 28.30 | 0.58 | 0.22 |
| rafter | 1.2G+1.5Qp | rafter L lower | 1.73 | 1.11 | 0.79 | -2.66 | 9.27 | 8.38 | 27.45 | 1.00 | 0.26 |
| tie | 1.2G+1.5Qc | ceiling joist | 1.08 | 0.63 | 0.61 | 1.20 | 13.53 | 26.09 | 27.45 | 0.77 | 0.80 |
| collar | 1.2G+1.5Q | collar tie | 1.03 | 0.05 | 0.71 | -3.71 | 3.84 | 3.84 | 26.60 | 0.93 | 0.12 |
| ridge | 1.2G+1.5Q | ridge beam | 0.87 | -0.89 | 1.03 | 0.00 | 25.05 | 12.34 | 55.01 | 0.36 | 0.19 |

Support reactions (kN; H = horizontal thrust):

| support | |H| max | V max (down) | V min (uplift if <0) |
|---|---|---|---|
| joist prop 1 (mid truss) | 0.00 | 1.17 | 0.36 |
| joist prop 2 (mid truss) | 0.00 | 0.44 | 0.22 |
| joist prop 3 (mid truss) | 0.00 | 0.54 | 0.36 |
| purlin on cross wall (L y=0) | 0.00 | 1.67 | -0.14 |
| purlin on cross wall (L y=12000) | 0.00 | 1.67 | -0.14 |
| purlin on cross wall (L y=4000) | 0.00 | 6.08 | -1.47 |
| purlin on cross wall (L y=8000) | 0.00 | 6.08 | -1.47 |
| purlin on cross wall (R y=0) | 0.00 | 0.20 | -1.60 |
| purlin on cross wall (R y=12000) | 0.00 | 0.20 | -1.60 |
| purlin on cross wall (R y=4000) | 0.00 | 1.92 | -5.50 |
| purlin on cross wall (R y=8000) | 0.00 | 1.92 | -5.50 |
| ridge on cross wall (y=0) | 0.00 | 0.77 | -0.53 |
| ridge on cross wall (y=12000) | 0.00 | 0.77 | -0.53 |
| ridge on cross wall (y=4000) | 0.00 | 3.30 | -2.17 |
| ridge on cross wall (y=8000) | 0.00 | 3.30 | -2.17 |
| wall L (mid truss) | 2.44 | 2.86 | -1.87 |
| wall R (mid truss) | 0.00 | 2.86 | -1.87 |

Serviceability deflections, mid-bay truss (mm; limits span/300: rafter 15.9, joist span 2125 → 7.1, purlin bay 4000 → 13.3):

| case | j2 | rafter_mm | lower_seg_mm | collar_node_mm | apex_mm | spread_mm | joist_sag_mm | purlin_mm |
|---|---|---|---|---|---|---|---|---|
| G long-term | 3 | -4.54 | -3.99 | -1.87 | -1.57 | 0.88 | -2.26 | -2.35 |
| 0.7Q short-term | 1 | -1.98 | -1.76 | -0.72 | -0.60 | 0.34 | 0.00 | -0.90 |
| Ws uplift | 1 | 4.68 | 4.24 | 1.42 | 1.10 | -0.60 | 0.00 | 1.76 |

Collar-tie lap: N* = 4.80 kN (compression, 1.2G+Wd) ≈ 15 x 3.15 mm nails each end (Q_k 0.515 kN J4, φ 0.80, k1 1.0, k17 0.8), or an M12 bolt.

![what-if: as built + collar braced at third points](collarbraced_35x105.png)

### Section sweep — as built (rafters/collar/joists/purlins all this section; ridge 40x190)

| section | rafter | collar | joist | purlin | ridge | rafter δG mm | purlin δG mm |
|---|---|---|---|---|---|---|---|
| 35x105 | 1.73 | 8.69 | 1.08 | 4.20 | 0.87 | 4.54 | 2.35 |
| 35x140 | 0.96 | 6.72 | 0.72 | 3.15 | 0.68 | 2.27 | 1.90 |
| 45x140 | 0.73 | 3.27 | 0.45 | 1.62 | 0.58 | 1.88 | 1.62 |
| 35x190 | 0.59 | 4.99 | 0.50 | 2.40 | 0.51 | 1.16 | 1.51 |
| 45x190 | 0.39 | 2.45 | 0.29 | 1.15 | 0.44 | 0.98 | 1.30 |
| 45x240 | 0.26 | 1.91 | 0.21 | 0.95 | 0.35 | 0.62 | 1.09 | 

