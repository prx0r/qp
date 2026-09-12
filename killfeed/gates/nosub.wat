;; NOSUB gate: (share, threshold, redesign) -> 1/0/-1.
;; FALSE: share>=t OR redesign==1. TRUE: share<t AND redesign==0.
(module
  (func (export "nosub")
    (param $sh f64) (param $t f64) (param $rd f64)
    (result i32)
    (if (result i32)
      (i32.or
        (f64.ge (local.get $sh) (local.get $t))
        (f64.eq (local.get $rd) (f64.const 1)))
      (then (i32.const 0))
      (else
        (if (result i32)
          (i32.and
            (f64.lt (local.get $sh) (local.get $t))
            (f64.eq (local.get $rd) (f64.const 0)))
          (then (i32.const 1))
          (else (i32.const -1)))))))
