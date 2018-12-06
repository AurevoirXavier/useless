extern crate rand;

// --- std ---
use std::thread::sleep;
use std::time::Duration;

// --- external ---
use rand::{
    Rng,
    thread_rng,
    seq::SliceRandom,
};

fn main() {
    let mut rng = thread_rng();

    let mut waits = {
        let mut v = vec![];
        let mut y = 36000;

        loop {
            let x = rng.gen_range(0, 6);
            if y < x {
                v.push(y);
                break;
            } else {
                y -= x;
                v.push(x);
            }
        }

        v[..v.len() / 100 * 100].to_vec()
    };
    let total = waits.len();
    let loop_times = total / 100;

//    {
//        println!("{}", loop_times);
//        assert!(loop_times > 140 && loop_times <= 145);
//
//        let sum = waits.iter().sum::<u64>();
//        println!("{}", sum);
//        assert!(sum > 35000 && sum <= 36000);
//    }

    let mut accounts = {
        let mut v = vec![];
        for i in 0u8..100 {
            let random_fund = rng.gen_range(4500u16, 5501) as f64;
            v.push((i, random_fund));
        }

        v
    };

    for account in accounts.iter() { println!("账号 {}, 登陆成功", account.0); }

    let accounts_ = {
        let mut v = vec![];
        for &(i, fund) in accounts.iter() {
            v.push((i, (fund / loop_times as f64).ceil()));
        }

        v
    };

    let mut count = 0;
    for _ in 0..loop_times {
        for &(i, reduce) in accounts_.choose_multiple(&mut rng, 100) {
            sleep(Duration::from_secs(waits.pop().unwrap()));
            waits.pop().unwrap();
            let ref mut account = accounts[i as usize];
            (*account).1 -= reduce;
            if account.1 < 0. { print!("账号 {}, 剩余资金 0", account.0); } else { print!("账号 {}, 剩余资金 {}", account.0, account.1); }
            count += 1;
            println!(", 总进度 {}/{}", count, total);
        }
    }
}
