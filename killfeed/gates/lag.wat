;; LAG gate: dates as YYYYMMDD numbers. (close, horizon) -> 1/0/-1.
;; TRUE: close > horizon (shortage persists). FALSE: closes inside.
(module
  (func (export "lag")
    (param $close f64) (param $hor f64)
    (result i32)
    (if (result i32) (f64.gt (local.get $close) (local.get $hor))
      (then (i32.const 1))
      (else
        (if (result i32) (f64.le (local.get $close) (local.get $hor))
          (then (i32.const 0))
          (else (i32.const -1)))))))
