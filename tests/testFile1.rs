// For testing AST Generation
fn main () {
    let mut a1:[bool; 4]=[!false, true&&false||true];
    let mut a2:[u8; 5]=[99+99; 2];
    let mut b:u32 = 1;
    // will cause overflow as b is unsigned.
    b = 1-2;
    a1[3+b] = a1[0+99] && a1[1];

    if 1>2&&a1[4+b*1] {
        b = 8;
    } else if b != 9999 {
        b = 1000;
    } else {
        b= 11;
    }

    let mut a1:i64 = (-5 * 99) + 8;

    while a1 < 7i64 {
        a1 = 555;
        if b != 8u32 {
            b = 999;
        } else {
            a1 = 777;
        }
    }
}
