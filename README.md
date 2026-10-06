# news-bias

An early exploratory repository for a project on bias in news coverage. The starting point is the Multi-News dataset (Fabbri et al., ACL 2019), in which each example groups several news articles about the same event together with a human-written summary. The repository does not record a formal research question; the setup (clusters of articles about one event, with per-cluster lists of source URLs) points toward comparing how different outlets cover the same story. So far it contains a single notebook that lists the raw Multi-News files and prints the first lines of the training sources and targets. No modeling has been done here.

## Layout

- `notebooks/2022-10-13__analyze-multi-news-dataset.ipynb` -- inspects the Multi-News files (`ls`, `head` of `train.src` and `train.tgt`).
- `data/` (gitignored) -- `multi-news-original-data/` with train/val/test `.src`/`.tgt` files (about 800 MB) and `multi-news-code-and-ids/`, a clone of the Multi-News GitHub repository containing article IDs, source-URL maps and the original baseline code.

## How to run

Place the Multi-News files under `data/multi-news-original-data/` and open the notebook in Jupyter. The notebook refers to `../data/multi-news-original/`, which does not match the on-disk directory name, so adjust the path first.

## Data

Not included. Multi-News is distributed by its authors at https://github.com/Alex-Fabbri/Multi-News (preprocessed and raw versions, plus scripts to rebuild it from the original article URLs). Terms of use follow the Newsroom dataset license; see the `LICENSE.txt` in the Multi-News repository.

## Status

All files date from a single day, 13 October 2022. The project was not developed further in this repository.
