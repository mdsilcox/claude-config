# Personal benchmark

No study compares lean and heavy Claude Code setups head to head. People's sense of their own speed is unreliable: in METR's 2025 trial, developers were 19 percent slower while believing they were 20 percent faster. So judge this setup on your own work, with numbers.

## Protocol
1. Pick three to five real tasks with different shapes: a bug fix, a small feature, a multi-file feature, a UI change, and a C++ or C# mod change.
2. Write each task's acceptance criteria first, so every run is judged the same way.
3. Run each task in a fresh session on a clean branch, under the configuration being tested.
4. Record the numbers below for each run.
5. Compare configurations on similar tasks, not identical ones: the second time through you already know the answer.

Repeat after a major model release or a big change to the setup.

## Results
| Date | Config | Task | Shape | 5h % used | Week % used | Wall time | Your time | Defects found in review | Defects after merge | Passed first review |
|---|---|---|---|---|---|---|---|---|---|---|

Read the five-hour and weekly percentages from the status line or `/usage` before and after each run.

## Vault recall log
Each time a vault note comes up, note whether it changed a decision. After a month, this shows whether the vault earns its keep.

| Date | Note | Changed a decision? | How |
|---|---|---|---|
