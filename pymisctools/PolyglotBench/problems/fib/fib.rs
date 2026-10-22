use std::io::{self, Read};
fn main() {
    let mut s = String::new();
    io::stdin().read_to_string(&mut s).unwrap();
    let n: u64 = s.trim().parse().unwrap();
    let mut a: u64 = 0;
    let mut b: u64 = 1;
    for _ in 0..n { let t = a; a = b; b = t + b; }
    println!("{}", a);
}
