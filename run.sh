set -e
python appeals_analysis/01_download_tournament_info.py
python appeals_analysis/02_download_results_and_controversials.py --date-from 2019-01-01 --date-to 2019-12-31
python appeals_analysis/02_download_results_and_controversials.py --date-from 2022-01-01 --date-to 2022-10-29