# ==========================================================================================
# P6 final re-run, step R1 (R): build ALL inputs of the remaining checks from the raw files, with R code only.
#   - the outcome panel (OECD Q661S via FRED, Japan before 1994 from the ESRI series), with Hong Kong and Taiwan added,
#     and the panel with the 2026 Eurostat series for 23 countries;
#   - for each of the 12 core episodes and each design variant: the window and the list of comparison countries.
# Then compares everything with what the Python code used (data/python_*.csv).
# Variants (tag): main, lead1, lead2 (treatment date 1 / 2 quarters earlier; post window lengthened by 1 / 2), hktw (HK, TW added),
#   esvint (Eurostat series), pre60, pre80, prefull (pre-window of 60 / 80 quarters / full history), restricted (comparison countries with
#   no rate change in the pre-treatment window as well), nobreakrule (data-break rule off).
# Rules (paper, Section 4): window = pre_n quarters before the treatment quarter + 20 from it; comparison countries = data in the whole window,
#   NO standard-rate change from the start of the rate-check period (the treatment quarter, or the first pre quarter if "restricted") to the last
#   post quarter (any row of vat_rate_changes.csv); MX (break 1993Q1), IE (2015Q1), GR (1990Q3) dropped if the break is inside the window
#   (unless the rule is off); at least 3 comparison countries; the treated series must be complete in the window.
# Run: setwd("<folder rerun_final_20261025>"); source("R/R1_build_inputs.R")
# Output: data_r/p6_wide_main_r.csv, data_r/p6_wide_es_r.csv, data_r/variants_r.csv, output/R1_check_variants.csv, output/R1_check_panels.csv
# ==========================================================================================
dir.create("data_r", showWarnings = FALSE); dir.create("output", showWarnings = FALSE)
qidx <- function(y, q) y * 4 + (q - 1)
d2q  <- function(d) qidx(as.integer(substr(d, 1, 4)), (as.integer(substr(d, 6, 7)) - 1) %/% 3 + 1)   # "1995-01-01"
s2q  <- function(s) qidx(as.integer(substr(s, 1, 4)), as.integer(substr(s, 6, 6)))                    # "2014Q2"
grid <- qidx(1960, 1):qidx(2023, 3); NG <- length(grid)

## ---- outcome panel from the raw FRED files ----------------------------------------------------
raw <- "data/raw_fred"
cc  <- sort(unique(substr(sub("NAEXKP02", "", list.files(raw, pattern = "^NAEXKP02")), 1, 2)))
rd  <- function(s) { x <- read.csv(file.path(raw, paste0(s, ".csv")), stringsAsFactors = FALSE)
                     v <- suppressWarnings(as.numeric(x[[2]])); k <- !is.na(v); setNames(v[k], d2q(x[[1]][k])) }
Y <- matrix(NA_real_, NG, length(cc), dimnames = list(grid, cc))
for (c in cc) { a <- rd(paste0("NAEXKP02", c, "Q661S")); b <- rd(paste0("NAEXKP01", c, "Q661S"))
                k <- intersect(names(a), names(b)); y <- log(a[k] / b[k]); k2 <- names(y) %in% rownames(Y); Y[names(y)[k2], c] <- y[k2] }
sp <- read.csv("data/panel_japan_spliced_20261015.csv", stringsAsFactors = FALSE)
Y[, "JP"] <- NA_real_; kq <- as.character(d2q(sp$date)); ok <- kq %in% rownames(Y); Y[kq[ok], "JP"] <- sp$y_lncons_minus_lngdp[ok]
Ymain <- Y

## ---- Hong Kong and Taiwan (files of the UK project; ln(consumption / GDP)) -------------------------
tw <- read.csv("data/tw_raw.csv", stringsAsFactors = FALSE); hk <- read.csv("data/hk_raw.csv", stringsAsFactors = FALSE)
TW <- setNames(log(tw[[3]] / tw[[2]]), s2q(tw$period))
HK <- setNames(log(hk[[3]] / hk[[2]]), qidx(as.integer(substr(hk$period, 1, 4)), (as.integer(substr(hk$period, 5, 6)) - 1) %/% 3 + 1))
Yhk <- cbind(Ymain, TW = NA_real_, HK = NA_real_)
Yhk[intersect(names(TW), rownames(Yhk)), "TW"] <- TW[intersect(names(TW), rownames(Yhk))]
Yhk[intersect(names(HK), rownames(Yhk)), "HK"] <- HK[intersect(names(HK), rownames(Yhk))]

## ---- Eurostat 2026 series for 23 countries ---------------------------------------------------------
es <- "data/raw_eurostat"; Yes <- Ymain
rde <- function(f) { x <- read.csv(f, stringsAsFactors = FALSE); setNames(x$value, qidx(as.integer(substr(x$period, 1, 4)), as.integer(substr(x$period, 7, 7)))) }
for (f in sort(list.files(es, pattern = "^cons_"))) {
  c <- substr(f, 6, 7); a <- rde(file.path(es, f)); b <- rde(file.path(es, paste0("gdp_", c, ".csv")))
  k <- intersect(names(a), names(b)); e <- log(a[k] / b[k]); Yes[, c] <- NA_real_; k2 <- names(e) %in% rownames(Yes); Yes[names(e)[k2], c] <- e[k2]
}
wr <- function(M, f) { W <- data.frame(t = grid - qidx(1960, 1), M, check.names = FALSE); names(W)[-1] <- paste0("c_", colnames(M)); write.csv(W, f, row.names = FALSE, na = "") }
wr(Yhk, "data_r/p6_wide_main_r.csv"); wr(Yes, "data_r/p6_wide_es_r.csv")

## ---- rate changes ---------------------------------------------------------------------------------
chg <- read.csv("data/vat_rate_changes.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM"); chg$q <- s2q(chg$quarter)
data_breaks <- c(MX = "1993Q1", IE = "2015Q1", GR = "1990Q3")

## ---- windows and comparison countries -----------------------------------------------------------------
make <- function(Yp, ep, pre_n, post_n, t0q, restricted = FALSE, break_rule = TRUE, donor_cols) {
  tr <- substr(ep, 1, 2); i0 <- which(grid == t0q)
  if (pre_n == "full") pre_n <- i0 - min(which(!is.na(Yp[, tr])))
  if (i0 - pre_n < 1 || i0 - 1 + post_n > NG) return(NULL)
  rows <- (i0 - pre_n):(i0 + post_n - 1); win <- grid[rows]
  if (anyNA(Yp[rows, tr])) return(NULL)
  lo <- if (restricted) win[1] else t0q; don <- c()
  for (c in setdiff(donor_cols, tr)) {
    if (anyNA(Yp[rows, c])) next
    if (any(chg$country == c & chg$q >= lo & chg$q <= win[length(win)])) next
    if (break_rule && c %in% names(data_breaks) && s2q(data_breaks[[c]]) %in% win) next
    don <- c(don, c)
  }
  if (length(don) < 3) return(NULL)
  list(w0 = win[1] - qidx(1960, 1), t2 = win[length(win)] - qidx(1960, 1), T0 = pre_n, donors = don)
}
core12 <- read.csv("data/core12.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")$episode
spec <- list(main = list(), lead1 = list(L = 1), lead2 = list(L = 2), hktw = list(panel = "hk"), esvint = list(panel = "es"),
             pre60 = list(pre = 60), pre80 = list(pre = 80), prefull = list(pre = "full"),
             restricted = list(restricted = TRUE), nobreakrule = list(break_rule = FALSE))
rows <- list()
for (tag in names(spec)) for (ep in core12) {
  s <- spec[[tag]]; L <- if (is.null(s$L)) 0 else s$L; pnl <- if (is.null(s$panel)) "main" else s$panel
  Yp <- switch(pnl, main = Ymain, hk = Yhk, es = Yes)
  r <- make(Yp, ep, if (is.null(s$pre)) 40 else s$pre, 20 + L, s2q(substring(ep, 3)) - L,
            restricted = isTRUE(s$restricted), break_rule = !identical(s$break_rule, FALSE), donor_cols = colnames(Yp))
  if (is.null(r)) { cat("no run:", tag, ep, "\n"); next }
  rows[[length(rows) + 1]] <- data.frame(ep = ep, tag = tag, panel = if (pnl == "es") "es" else "main", cc = substr(ep, 1, 2),
                                         w0 = r$w0, t2 = r$t2, T0 = r$T0, J = length(r$donors), donors = paste(r$donors, collapse = " "))
}
V <- do.call(rbind, rows); write.csv(V, "data_r/variants_r.csv", row.names = FALSE)

## ---- comparison with the Python files -------------------------------------------------------------------
P <- read.csv("data/python_variants_all.csv", stringsAsFactors = FALSE)
m <- merge(V, P, by = c("ep", "tag"), all = TRUE, suffixes = c("_R", "_py"))
m$same_run   <- !is.na(m$J_R) & !is.na(m$J_py)
m$same_window <- m$same_run & m$w0_R == m$w0_py & m$t2_R == m$t2_py & m$T0_R == m$T0_py
m$same_donors <- m$same_run & mapply(function(a, b) setequal(strsplit(a, " ")[[1]], strsplit(b, " ")[[1]]), m$donors_R, m$donors_py)
chk <- m[, c("ep", "tag", "same_run", "same_window", "same_donors", "J_R", "J_py")]
write.csv(chk, "output/R1_check_variants.csv", row.names = FALSE)
cat("\nRuns: R", nrow(V), " Python", nrow(P), "\n"); print(table(tag = chk$tag, all_equal = chk$same_run & chk$same_window & chk$same_donors))
## panels
cmp <- function(M, f) { Pw <- read.csv(f, check.names = FALSE); Pw[intersect(names(Pw), c("t", "year", "quarter"))] <- NULL; nm <- sub("^c_", "", names(Pw)); out <- c()
  for (j in seq_along(nm)) { x <- M[, nm[j]]; y <- Pw[[j]]; same_na <- all(is.na(x) == is.na(y)); d <- if (any(!is.na(x) & !is.na(y))) max(abs(x - y), na.rm = TRUE) else 0
                             out <- rbind(out, data.frame(series = nm[j], same_missing_pattern = same_na, max_abs_diff = d)) }
  out }
ck <- rbind(cbind(panel = "main (with HK, TW)", cmp(Yhk, "data/python_wide_main.csv")), cbind(panel = "Eurostat", cmp(Yes, "data/python_wide_esvint.csv")))
write.csv(ck, "output/R1_check_panels.csv", row.names = FALSE)
cat("\nPanels: series with a different missing pattern:", sum(!ck$same_missing_pattern), "; largest difference:", max(ck$max_abs_diff), "\n")
cat("Expected: every run 'all_equal' TRUE, no different missing pattern, largest difference below 1e-8 (the python_wide files are rounded to 12 digits).\n")
