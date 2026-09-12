;; WTP gate: (price, qty, x, y) -> 1/0/-1.
;; TRUE: price>=x AND qty>-y. FALSE: price>=x AND qty<=-y. Else UNKNOWN.
(module
  (func (export "wtp")
    (param $pr f64) (param $qy f64) (param $x f64) (param $y f64)
    (result i32)
    (if (result i32)
      (i32.and
        (f64.ge (local.get $pr) (local.get $x))
        (f64.gt (local.get $qy) (f64.neg (local.get $y))))
      (then (i32.const 1))
      (else
        (if (result i32)
          (i32.and
            (f64.ge (local.get $pr) (local.get $x))
            (f64.le (local.get $qy) (f64.neg (local.get $y))))
          (then (i32.const 0))
          (else (i32.const -1)))))))
