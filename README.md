# capture_enyaq_charge

Small Python script that uses skodaconnect (from https://github.com/lendy007/skodaconnect) to connect to the Skoda Enyaq iV to collect charging status.

The script allows output to csv files and/or sending data to InfluxDb/Telegraf

## Prerequisites

* Python 3.x (e.g. via Miniconda https://docs.conda.io/en/latest/miniconda.html)
* pip
* An account with SkodaConnect (Check that the SkodaConnect app works for you)
* Car in online mode

## Setup

* Edit the config.ini file with your username and password. By default, logs will get stored in the logs folder. You can change this folder in the config file if needed.
* Make sure you have any prerequisites installed
`pip install -r requirements.txt`

## Usage

You can now run the application with the command 
`python main.py`

You can override options from config.ini by providing command-line arguments, e.g.
`python main.py --username the@answer.is.42.com`


