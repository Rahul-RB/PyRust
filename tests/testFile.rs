// For testing AST Generation
fn main () {
    let mut a1:[bool; 4]=[!false, true&&false||true];
    let mut a2:[f64; 5]=[99.87+99.1; 2];
    let mut b:i32 = 1;
    b = -1;
    a1[3+b] = a1[0+99] && a1[1];

    if 1>2&&a1[4+b*1] {
        b = 8;
    } else {
        b = 1000;
    }

    let mut a1:i64 = (-5 * 99) + 8;

    while a1 < 7i64 {
        a1 = 555;
        if b != 8i32 {
            b = 999;
        } else {
            a1 = 777;
        }
    }
}

// // For testing parser
// fn main(){
//     let a:i32 = -(99 + 6) / 19 % 3;
//     let c:i32 = a;
//     // let c:i16 = b;
//     // ^ Will fail as b not declared
//     let c:i32 = 99;
//     let mut c:i64 = 99;
//     let isNotBool:bool = !(999 > 8);
//     c = 10;
//     while isNotBool {
//         let b:i32 = 69;
//         let d:i64 = 69;
//         let isBool:bool = false;
//         {
//             let mut b1:i32 = 69;
//             let b2:i32 = 69;
//             let b3:i32 = 69;
//             b1 = 9;
//             // b4 = 10;
//             // ^ Will fail as b4 not declared
//         }
//         // b1 = 9;
//         // ^ Will fail as b1 not declared in current scope
//     }
// }
