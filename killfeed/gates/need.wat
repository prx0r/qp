;; NEED gate: (intensity, min, relevant, kill) -> 1/0/-1.
;; TRUE: intensity>=min AND relevant==1. FALSE: intensity<kill OR
;; relevant==0. Else UNKNOWN (incl. any NaN).
(module
  (func (export "need")
    (param $in f64) (param $mn f64) (param $rel f64) (param $kill f64)
    (result i32)
    (if (result i32) (f64.ne (local.get $in) (local.get $in))
      (then (i32.const -1))
      (else
        (if (result i32)
          (i32.and
            (f64.ge (local.get $in) (local.get $mn))
            (f64.eq (local.get $rel) (f64.const 1)))
          (then (i32.const 1))
          (else
            (if (result i32)
              (i32.or
                (f64.lt (local.get $in) (local.get $kill))
                (f64.eq (local.get $rel) (f64.const 0)))
              (then (i32.const 0))
              (else (i32.const -1)))))))))
