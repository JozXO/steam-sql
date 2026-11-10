| Query | Check                                                                            | Expected                          | SQL result                        | Match |
|-------|----------------------------------------------------------------------------------|-----------------------------------|-----------------------------------|-------|
| Q1    | Reviews collected                                                                | 218,380                           | 218,380                           | yes   |
| Q2    | Reviews in the shared window (dashboard data_quality)                            | 169,612                           | 169,612                           | yes   |
| Q2    | Reviews removed as review bomb (dashboard data_quality)                          | 54,873                            | 54,873                            | yes   |
| Q2    | Reviews after window and review-bomb removal                                     | 114,739                           | 114,739                           | yes   |
| Q2    | Percent of all reviews removed                                                   | 47.5                              | 47.5                              | yes   |
| Q3    | Review-bomb table (apex_review_bombs.csv): every row and column identical        | 12 rows                           | 12 rows                           | yes   |
| Q3    | Simplified script, July 2024: times normal volume                                | 14.9                              | 14.9                              | yes   |
| Q3    | Simplified script, July 2024: positive %                                         | 8.8                               | 8.8                               | yes   |
| Q4    | Apex English positive %                                                          | 76.6                              | 76.6                              | yes   |
| Q4    | Apex Traditional script positive %                                               | 40.1                              | 40.1                              | yes   |
| Q4    | Apex gap, English minus Traditional script (points)                              | 36.5                              | 36.5                              | yes   |
| Q4    | English lifetime reviews                                                         | 450,786                           | 450,786                           | yes   |
| Q5    | Simplified script gap with bomb (points)                                         | 20.8                              | 20.8                              | yes   |
| Q5    | Simplified script gap without bomb (points)                                      | 4.1                               | 4.1                               | yes   |
| Q5    | japanese: gap with / without bomb (apex_gap_bomb_effect.csv)                     | 16.7 / 18.1                       | 16.7 / 18.1                       | yes   |
| Q5    | koreana: gap with / without bomb (apex_gap_bomb_effect.csv)                      | 3.3 / -0.9                        | 3.3 / -0.9                        | yes   |
| Q5    | schinese: gap with / without bomb (apex_gap_bomb_effect.csv)                     | 20.8 / 4.1                        | 20.8 / 4.1                        | yes   |
| Q5    | tchinese: gap with / without bomb (apex_gap_bomb_effect.csv)                     | 27.9 / 23.1                       | 27.9 / 23.1                       | yes   |
| Q6    | Language values in the baseline (6 languages + 'all')                            | 7                                 | 7                                 | yes   |
| Q10   | Games in the baseline                                                            | 14                                | 14                                | yes   |
| Q10   | Apex has the widest Traditional script gap of 14 games (rank)                    | 1                                 | 1                                 | yes   |
| Q10   | Traditional script gap, all 14 games (gaps_by_game.csv)                          | 14 of 14                          | 14 of 14                          | yes   |
| Q9    | Control chart flags Korean July and August 2024 (both are in the bomb table)     | flagged                           | flagged                           | yes   |
| Q11   | Monthly series rows (5 languages x 23 months)                                    | 115                               | 115                               | yes   |
| Q11   | Series values (reviews, positive %) identical to pandas, all rows                | 115 of 115                        | 115 of 115                        | yes   |
| Q11   | Series runs October 2024 to August 2026, no July to September 2024               | 2024-10 to 2026-08, 0 bomb months | 2024-10 to 2026-08, 0 bomb months | yes   |
| Q12   | Forecast rows: 5 languages x 2 measures x (11 + 9) target months                 | 200                               | 200                               | yes   |
| Q12   | Naive forecasts identical to pandas, all rows                                    | 200 of 200                        | 200 of 200                        | yes   |
| Q12   | Seasonal naive forecasts identical to pandas, all rows                           | 200 of 200                        | 200 of 200                        | yes   |
| Q12   | 3-month moving average forecasts identical to pandas, all rows                   | 200 of 200                        | 200 of 200                        | yes   |
| SES   | SES forecasts and chosen alpha identical to pandas (.ewm), all rows              | 200 of 200                        | 200 of 200                        | yes   |
| SES   | SES level, loop vs weighted-average formula (English volume, alpha 0.3)          | 2,794.3                           | 2,794.3                           | yes   |
| SES   | SES with alpha = 1 gives the last value (= naive)                                | 3,184.0                           | 3,184.0                           | yes   |
| Q13   | Backtest scores (MAE, MAPE, vs naive), 80 rows, identical to pandas              | 80 of 80                          | 80 of 80                          | yes   |
| Q13   | English volume MAE, 1 month ahead, naive (reviews)                               | 406.1                             | 406.1                             | yes   |
| Q13   | English volume MAE, 1 month ahead, ses (reviews)                                 | 424.8                             | 424.8                             | yes   |
| Q13   | English positive share MAE, 1 month ahead, naive (points)                        | 3.0                               | 3.0                               | yes   |
| Q13   | English positive share MAE, 1 month ahead, ses (points)                          | 2.7                               | 2.7                               | yes   |
| Q14   | Languages beating naive, per measure, horizon and model (12 rows)                | 12 of 12                          | 12 of 12                          | yes   |
| Q15   | Plan vs actual, last 6 months (60 rows): actual and SES plan identical to pandas | 60 of 60                          | 60 of 60                          | yes   |
