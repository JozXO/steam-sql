| Query | Check                                                                        | Published   | SQL result  | Match |
|-------|------------------------------------------------------------------------------|-------------|-------------|-------|
| Q1    | Reviews collected                                                            | 218,380     | 218,380     | yes   |
| Q2    | Reviews in the shared window (dashboard data_quality)                        | 169,612     | 169,612     | yes   |
| Q2    | Reviews removed as review bomb (dashboard data_quality)                      | 54,873      | 54,873      | yes   |
| Q2    | Reviews after window and review-bomb removal                                 | 114,739     | 114,739     | yes   |
| Q2    | Percent of all reviews removed                                               | 47.5        | 47.5        | yes   |
| Q3    | Review-bomb table (apex_review_bombs.csv): every row and column identical    | 12 rows     | 12 rows     | yes   |
| Q3    | Simplified script, July 2024: times normal volume                            | 14.9        | 14.9        | yes   |
| Q3    | Simplified script, July 2024: positive %                                     | 8.8         | 8.8         | yes   |
| Q4    | Apex English positive %                                                      | 76.6        | 76.6        | yes   |
| Q4    | Apex Traditional script positive %                                           | 40.1        | 40.1        | yes   |
| Q4    | Apex gap, English minus Traditional script (points)                          | 36.5        | 36.5        | yes   |
| Q4    | English lifetime reviews                                                     | 450,786     | 450,786     | yes   |
| Q5    | Simplified script gap with bomb (points)                                     | 20.8        | 20.8        | yes   |
| Q5    | Simplified script gap without bomb (points)                                  | 4.1         | 4.1         | yes   |
| Q5    | japanese: gap with / without bomb (apex_gap_bomb_effect.csv)                 | 16.7 / 18.1 | 16.7 / 18.1 | yes   |
| Q5    | koreana: gap with / without bomb (apex_gap_bomb_effect.csv)                  | 3.3 / -0.9  | 3.3 / -0.9  | yes   |
| Q5    | schinese: gap with / without bomb (apex_gap_bomb_effect.csv)                 | 20.8 / 4.1  | 20.8 / 4.1  | yes   |
| Q5    | tchinese: gap with / without bomb (apex_gap_bomb_effect.csv)                 | 27.9 / 23.1 | 27.9 / 23.1 | yes   |
| Q6    | Language values in the baseline (6 languages + 'all')                        | 7           | 7           | yes   |
| Q10   | Games in the baseline                                                        | 14          | 14          | yes   |
| Q10   | Apex has the widest Traditional script gap of 14 games (rank)                | 1           | 1           | yes   |
| Q10   | Traditional script gap, all 14 games (gaps_by_game.csv)                      | 14 of 14    | 14 of 14    | yes   |
| Q9    | Control chart flags Korean July and August 2024 (both are in the bomb table) | flagged     | flagged     | yes   |
