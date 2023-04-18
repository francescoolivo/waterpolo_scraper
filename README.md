# Waterpolo Scraper

_Waterpolo Scraper_ is a web crawler for downloading and querying international waterpolo data from the web.

## Supported leagues
At the time being, supported leagues are:
- Champions League (**LEN**)
- World Cup (**WC**)
- European Championship (**EC**)

## Usage

### Installation

First, clone this repo on your machine and move to the project directory:
```shell
git clone https://github.com/francescoolivo/waterpolo_scraper.git
cd waterpolo_scraper
```

Or, if you don't have git installed, you can simply download the zip and unzip it.

Now create a conda environment and activate it:
```shell
conda env create -f environment.yml
conda activate waterpolo_scraper
```

If you want to call the environment with a different name, you just have to change the environment name in the first line of the `environment.yml` file.

### Run

As a fundamental premise, scraping data from the internet is the biggest source of unexpected exceptions, errors and wrong data that you could ever imagine.
Therefore, expect some wrong data, missing values and outliers. I am doing my best to catch all possible errors and solve them, so if you notice a weird behavior just tell me or open an Issue, and I'll do my best to fix it as soon as possible.

The download interface is pretty straightforward, if you are not already in the repo root directory go there by using

```shell
cd waterpolo_scraper
```

Where you will find the run.py file. It takes two mandatory arguments, a list of leagues (-l or --leagues) and the writer to use (-w or --writer).

It also takes in a bunch of possible filters, which you can read about by typing

```shell
python run.py -h
```

#### Examples

These are some example of how to use the downloader:

- To download the 2022-23 Champions League (LEN) in csv format:
```shell
python run.py -s 22-23 -l LEN -w csv
```
or
```shell
python run.py --seasons 2022-2023 --leagues LEN --writer csv
```

