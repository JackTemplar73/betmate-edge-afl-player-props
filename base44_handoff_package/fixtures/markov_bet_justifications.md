# Markov Bet Justifications

Scope: A_BET and B_BET rows from `oddsapi_wheelo_ev_qi.csv`.

State path format: Projection support -> Probability edge -> Price/EV state -> QI confidence.

## 1. A_BET - Hayden McLean Goals Over 2.5 @ 14.0

- Book: Ladbrokes
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 3.0, probability 72.2%, market 7.1%, EV 910.5%, QI 92.0
- Portfolio: PORTFOLIO_BET; stake 0.5u; alt-line score 5.37921
- Ladder: Over 2.5 @ 14.0 EV 910.5%; Over 1.5 @ 4.25 EV 308.5%
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 3.0 goals avg against a 2.5 line, creating a +0.5 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 92.0 QI. Model probability is 72.2% versus market 7.1%, producing 910.5% EV.
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

## 2. A_BET - Liam Fawcett Goals Over 1.5 @ 4.0

- Book: Betr
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 2.129, probability 77.0%, market 25.0%, EV 208.1%, QI 95.0
- Portfolio: PORTFOLIO_BET; stake 0.5u; alt-line score 1.33324
- Ladder: Over 1.5 @ 4.0 EV 208.1%; Over 0.5 @ 1.64 EV 59.5%
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 2.129 goals avg against a 1.5 line, creating a +0.6 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 95.0 QI. Model probability is 77.0% versus market 25.0%, producing 208.1% EV.
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

## 3. A_BET - Noah Roberts-Thomson Goals Over 0.5 @ 2.4

- Book: SportsBet
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 1.5, probability 88.0%, market 41.7%, EV 111.3%, QI 93.5
- Portfolio: PORTFOLIO_BET; stake 0.5u; alt-line score 0.77532
- Ladder: Over 0.5 @ 2.4 EV 111.3%; Over 1.5 @ 9.25 EV 362.5%
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 1.5 goals avg against a 0.5 line, creating a +1.0 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 88.0% versus market 41.7%, producing 111.3% EV.
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

## 4. A_BET - Dion Prestia Disposals Under 22.5 @ 1.87

- Book: PointsBet (AU)
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 17.432, probability 82.2%, market 50.0%, EV 53.6%, QI 93.5
- Portfolio: PORTFOLIO_BET; stake 1.0u; alt-line score 0.4411
- Ladder: No higher-ranked alternate retained.
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 17.432 disposals against a 22.5 line, creating a +5.1 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 82.2% versus market 50.0%, producing 53.6% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

## 5. A_BET - Sullivan Robey Disposals Under 20.5 @ 1.87

- Book: PointsBet (AU)
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 16.728, probability 75.4%, market 50.0%, EV 40.9%, QI 93.5
- Portfolio: PORTFOLIO_BET; stake 1.0u; alt-line score 0.3154
- Ladder: No higher-ranked alternate retained.
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 16.728 disposals against a 20.5 line, creating a +3.8 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 75.4% versus market 50.0%, producing 40.9% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

## 6. A_BET - Tom McCarthy Disposals Under 25.5 @ 1.95

- Book: SportsBet
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 22.304, probability 71.9%, market 47.9%, EV 40.3%, QI 95.0
- Portfolio: PORTFOLIO_BET; stake 1.0u; alt-line score 0.3078
- Ladder: No higher-ranked alternate retained.
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 22.304 disposals against a 25.5 line, creating a +3.2 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 95.0 QI. Model probability is 71.9% versus market 47.9%, producing 40.3% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

## 7. A_BET - Mabior Chol Tackles Over 1.5 @ 1.87

- Book: PointsBet (AU)
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 2.879, probability 74.4%, market 53.5%, EV 39.2%, QI 96.0
- Portfolio: PORTFOLIO_BET; stake 0.8u; alt-line score 0.27732
- Ladder: Over 1.5 @ 1.87 EV 39.2%; Over 3.5 @ 8.0 EV 207.0%; Over 2.5 @ 3.0 EV 71.5%
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 2.879 tackles against a 1.5 line, creating a +1.4 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 96.0 QI. Model probability is 74.4% versus market 53.5%, producing 39.2% EV.
- Main risk: Tackle props depend on game script and pressure exposure.

## 8. A_BET - Kyle Langford Disposals Under 20.5 @ 1.87

- Book: PointsBet (AU)
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 17.148, probability 72.9%, market 50.0%, EV 36.3%, QI 93.5
- Portfolio: PORTFOLIO_BET; stake 1.0u; alt-line score 0.2729
- Ladder: No higher-ranked alternate retained.
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 17.148 disposals against a 20.5 line, creating a +3.4 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 72.9% versus market 50.0%, producing 36.3% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

## 9. A_BET - Hugh McCluggage Disposals Under 22.5 @ 1.89

- Book: SportsBet
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 19.357, probability 71.6%, market 49.3%, EV 35.4%, QI 95.0
- Portfolio: PORTFOLIO_BET; stake 1.0u; alt-line score 0.2692
- Ladder: No higher-ranked alternate retained.
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 19.357 disposals against a 22.5 line, creating a +3.1 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 95.0 QI. Model probability is 71.6% versus market 49.3%, producing 35.4% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

## 10. A_BET - Bradley Hill Disposals Over 18.5 @ 1.87

- Book: Ladbrokes
- Markov path: Strong -> Dominant -> Mispriced -> Elite | score 12/12
- Model: projection 21.663, probability 71.7%, market 50.0%, EV 34.2%, QI 96.5
- Portfolio: PORTFOLIO_BET; stake 1.0u; alt-line score 0.26716
- Ladder: Over 18.5 @ 1.87 EV 34.2%; Over 19.5 @ 1.95 EV 27.3%
- Decision: A-grade: model, price, and QI all confirm.
- Justification: Model data projects 21.663 disposals against a 18.5 line, creating a +3.2 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 96.5 QI. Model probability is 71.7% versus market 50.0%, producing 34.2% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.
