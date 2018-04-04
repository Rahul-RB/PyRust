// For testing AST Generation
fn main () {
    let mut a1:[bool; 4]=[false, true];
    let mut a2:[f32; 5]=[99.87; 2];
    let mut b:i32 = 1;
    b = -1;
    a1[3+b] = 32.98f64;

    let mut a1:i64 = (-5 * 99) + 8;

    while a1 < b {
        a1 = 555;
        if b != a1 {
            b = 999;
        } else {
            a1 = 777;
        }
    }
}

// // For testing parser
// fn main(){
//     let a:i32 = -(99 + 6) / 19 % 3;
//     let c:i16 = a;
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
