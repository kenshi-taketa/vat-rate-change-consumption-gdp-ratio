# P6 Python コード(コメント付き)2026-10-21
コメントは日本語です。**計算の部分は1文字も変えていません**(元のファイルとプログラムの構文木が同じであることを確認済み)。

## 読む順序
1. `p6est.py`(約170行): 推定の中心。データ読み込み → 比較国の選び方 → SCM の重み → ridge 補正(ASCM)→ 1エピソードの推定とプラセボ。
2. `run_stage4.py`: 全エピソードを実行して結果(pickle)を保存する。
3. `aggregate_stage4.py`: 11件(核増税)をまとめる順列検定、層別、1件ずつ除く、仕様曲線。
4. `stage4_extra.py`: 拡張標本の分け方別の集計、Table 3 の下の行(ユーロ危機や日本2014を除く)、図。
5. `conformal_core.py`、`cft_core.py`: エピソード別の区間(conformal / scpi)。

## 注意
- `aggregate_stage4.py` と `stage4_extra.py` は、2.5%点と 97.5%点(本文 Table 3 の95%範囲)を出す版です(range95_20261021 の版と同じ。構文木が一致)。
- `stage4_extra.py` は同じフォルダの `aggregate_stage4.py` を読み込むので、2つを同じフォルダに置いて実行してください。
- Windows の Python は、標準では日本語の旧規格(cp932)でファイルを読みます。`stage4_extra.py` は `aggregate_stage4.py` を読むので、その読み込みだけ UTF-8 を明示しました(2026-10-21、再実行でエラーが出たため。計算は変わりません)。他は問題ありません。
- 必要なもの: Python 3、numpy、pandas、scipy、matplotlib、scpi_pkg(`cft_core.py` のみ)。

## 再実行の手順(投稿前)
引数の意味は各ファイルの冒頭のコメントにあります。入力の場所はあなたの PC に合わせて決めてください(確認が必要)。
1. `python run_stage4.py RAW SPL VAT EPI CORE OUT 2`
   RAW = raw_fred_20261015、SPL = panel_japan_spliced_20261015.csv、VAT = vat_rate_changes.csv、EPI = episode_candidates.csv、CORE = core_episodes_20261015.csv、OUT = 新しい出力フォルダ(基準の stage4\out とは別にする)。
2. `python aggregate_stage4.py OUT EPI CORE MOT 100000`(MOT = P6_core14_announcement_motive_20261015.csv)
3. `python stage4_extra.py OUT EPI CORE MOT`
4. `python compare_rerun.py 基準のOUT 新しいOUT` で、保存してある結果と比べる。
   決まった計算は 1e-8 未満の差で一致、順列検定の値は 0.03 以内で許容。
   (基準の stage4\out の拡張標本の順列検定の値は、今回の再計算と最大 0.015 ずれた。核11件の値は完全に一致。理由は未確認。)
