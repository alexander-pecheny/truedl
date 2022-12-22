set -e
python -m appeals_analysis.01_download_tournament_info
python -m appeals_analysis.02_download_results_and_controversials --date-from 2019-01-01 --date-to 2019-12-31
python -m appeals_analysis.02_download_results_and_controversials --date-from 2022-01-01 --date-to 2022-10-29

python -m appeals_analysis.03_tournament_stats --date-from 2019-01-01 --date-to 2019-12-31
python -m appeals_analysis.03_tournament_stats --date-from 2022-01-01 --date-to 2022-10-29
#  тут руками выбирается топ нефраншизных турниров из топов за 2019 и 2022