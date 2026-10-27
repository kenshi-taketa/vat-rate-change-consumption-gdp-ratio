# ==========================================================================================
# P6 re-run A (R): rebuild the gsynth input windows from the RAW FRED files, with R code only,
# compare them with the files written by the Python code (ep_<episode>.csv), then run gsynth.
# Purpose: remove "the data for gsynth were prepared by Python" from the limits of the re-estimation.
#
# Folder layout expected (edit ROOT and EPDIR below):
#   ROOT   = ...\消費増税の下方屈折効果_国際パネル        (contains raw_fred_20261015\, panel_japan_spliced_20261015.csv, vat_rate_changes.csv)
#   EPDIR  = ROOT\stage6_20261015\gsynth_check_20261021   (contains ep_<episode>.csv written by Python)
# Rules copied from the paper (Section 4), NOT from the Python code:
#   outcome y = ln(real consumption) - ln(real GDP), OECD Q661S via FRED (NAEXKP02 / NAEXKP01); Japan before 1994 from the
#   ESRI series (panel_japan_spliced file, column y_lncons_minus_lngdp); window = 40 quarters before the rate change + 20 from it;
#   donors = countries with data in the whole window and NO standard-rate change from the treatment quarter to the last post quarter
#   (any row of vat_rate_changes.csv); MX (break 1993Q1), IE (2015Q1) and GR (1990Q3) are dropped if the break is inside the window;
#   every series is rebased to 0 at the first pre quarter.
# Output: A_window_check.csv (donor lists and maximum difference of the data) and A_gsynth_results.csv.
# ==========================================================================================
ROOT  <- Sys.getenv("P6_ROOT", unset = getwd())   # folder that holds raw_fred_20261015/, vat_rate_changes.csv, ... (set P6_ROOT or setwd first)
EPDIR <- file.path(ROOT, "stage6_20261015/gsynth_check_20261021")
OUT   <- getwd()
eps <- c("JP2014Q2", "DE2007Q1", "NL2012Q4", "HU2012Q1", "LU2015Q1")
r_own <- c(JP2014Q2 = 4, DE2007Q1 = 5, NL2012Q4 = 3, HU2012Q1 = 5, LU2015Q1 = 4)   # factors chosen by our own code (stage 5)
data_breaks <- c(MX = "1993Q1", IE = "2015Q1", GR = "1990Q3")

qidx <- function(y, q) y * 4 + (q - 1)                       # quarter index
d2q  <- function(d) qidx(as.integer(substr(d, 1, 4)), (as.integer(substr(d, 6, 7)) - 1) %/% 3 + 1)
s2q  <- function(s) qidx(as.integer(substr(s, 1, 4)), as.integer(substr(s, 6, 6)))   # "2014Q2"

## ---- 1. outcome series from the raw files -------------------------------------------------
raw <- file.path(ROOT, "raw_fred_20261015")
cc  <- sort(unique(substr(sub("NAEXKP02", "", list.files(raw, pattern = "^NAEXKP02")), 1, 2)))
rd  <- function(s) { x <- read.csv(file.path(raw, paste0(s, ".csv")), stringsAsFactors = FALSE)
                     v <- suppressWarnings(as.numeric(x[[2]])); k <- !is.na(v); setNames(v[k], d2q(x[[1]][k])) }
grid <- qidx(1960, 1):qidx(2023, 3)
Y <- matrix(NA_real_, length(grid), length(cc), dimnames = list(grid, cc))
for (c in cc) {
  a <- rd(paste0("NAEXKP02", c, "Q661S")); b <- rd(paste0("NAEXKP01", c, "Q661S"))
  k <- intersect(names(a), names(b)); y <- log(a[k] / b[k])
  Y[names(y)[names(y) %in% rownames(Y)], c] <- y[names(y) %in% rownames(Y)]
}
sp <- read.csv(file.path(ROOT, "panel_japan_spliced_20261015.csv"), stringsAsFactors = FALSE)
Y[, "JP"] <- NA_real_; kq <- as.character(d2q(sp$date)); ok <- kq %in% rownames(Y)
Y[kq[ok], "JP"] <- sp$y_lncons_minus_lngdp[ok]

## ---- 2. rate changes ---------------------------------------------------------------------
chg <- read.csv(file.path(ROOT, "vat_rate_changes.csv"), stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")
chg$q <- s2q(chg$quarter)

## ---- 3. windows, donors, comparison with Python's files ------------------------------------------
build <- function(e) {
  tr <- substr(e, 1, 2); t0 <- s2q(substring(e, 3)); i0 <- which(grid == t0)
  win <- grid[(i0 - 40):(i0 + 19)]; stopifnot(length(win) == 60)
  stopifnot(!anyNA(Y[as.character(win), tr]))
  don <- c()
  for (c in setdiff(cc, tr)) {
    if (anyNA(Y[as.character(win), c])) next
    if (any(chg$country == c & chg$q >= t0 & chg$q <= win[60])) next
    if (c %in% names(data_breaks) && s2q(data_breaks[[c]]) %in% win) next
    don <- c(don, c)
  }
  W <- Y[as.character(win), c(tr, don), drop = FALSE]
  W <- sweep(W, 2, W[1, ], "-")                              # rebase to 0 at the first pre quarter
  colnames(W)[1] <- "treated"
  list(W = W, donors = don)
}
chk <- list(); res <- list()
for (e in eps) {
  b <- build(e); p <- read.csv(file.path(EPDIR, paste0("ep_", e, ".csv")), check.names = FALSE)
  pd <- setdiff(names(p), c("t", "post", "treated"))
  same_set <- setequal(pd, b$donors)
  mx <- if (same_set) max(abs(as.matrix(p[, c("treated", b$donors)]) - b$W[, c("treated", b$donors)])) else NA
  chk[[e]] <- data.frame(ep = e, J_R = length(b$donors), J_python = length(pd), same_donor_set = same_set,
                         only_in_R = paste(setdiff(b$donors, pd), collapse = " "), only_in_python = paste(setdiff(pd, b$donors), collapse = " "),
                         max_abs_diff_data = mx)
  print(chk[[e]])
}
write.csv(do.call(rbind, chk), file.path(OUT, "A_window_check.csv"), row.names = FALSE)
cat("\nCheck: same_donor_set must be TRUE and max_abs_diff_data below 1e-6 for all five episodes.\n")

## ---- 4. gsynth on the windows built in R (same settings as gsynth_check_p6_v4.R) -------------------
for (p in c("gsynth")) if (!requireNamespace(p, quietly = TRUE)) install.packages(p)
library(gsynth)
for (e in eps) {
  b <- build(e); W <- b$W; D <- ifelse(seq_len(60) > 40, 1, 0)
  long <- rbind(data.frame(id = "TREATED", t = 1:60, y = W[, "treated"], D = D),
                do.call(rbind, lapply(b$donors, function(j) data.frame(id = j, t = 1:60, y = W[, j], D = 0))))
  gap <- function(out) { k <- which(colnames(out$eff) == "TREATED"); stopifnot(length(k) == 1)
                         as.numeric(out$Y.dat[, k] - out$Y.ct[, k]) }
  set.seed(20261015)
  o1 <- gsynth(y ~ D, data = long, index = c("id", "t"), force = "two-way", CV = TRUE, r = c(0, 5), se = FALSE, estimator = "ife", min.T0 = 5)
  g1 <- gap(o1)
  o2 <- gsynth(y ~ D, data = long, index = c("id", "t"), force = "two-way", CV = FALSE, r = r_own[[e]], se = FALSE, estimator = "ife")
  g2 <- gap(o2)
  res[[e]] <- data.frame(ep = e, J = length(b$donors), r_gsynth = o1$r.cv, mean_gap_pp = 100 * mean(g1[41:60]), pre_rmspe_pp = 100 * sqrt(mean(g1[1:40]^2)),
                         r_own = r_own[[e]], mean_gap_pp_r_own = 100 * mean(g2[41:60]), pre_rmspe_pp_r_own = 100 * sqrt(mean(g2[1:40]^2)))
  print(res[[e]])
}
tab <- do.call(rbind, res); write.csv(tab, file.path(OUT, "A_gsynth_results.csv"), row.names = FALSE)
prev <- data.frame(ep = eps, r_prev = c(4, 0, 1, 0, 2), mean_gap_prev = c(-0.04811, -1.93401, 0.10305, -1.39748, 0.03759))
m <- merge(tab, prev, by = "ep"); m$diff_pp <- m$mean_gap_pp - m$mean_gap_prev
cat("\nComparison with the earlier gsynth run (data prepared by Python):\n"); print(m[, c("ep", "r_gsynth", "r_prev", "mean_gap_pp", "mean_gap_prev", "diff_pp")])
cat("\nIf the data match (A_window_check.csv) and diff_pp is about 0, the gsynth numbers do not depend on how Python prepared the data.\n")
