extern crate calamine;
extern crate reqwest;
extern crate url;

struct GoodsDetector(reqwest::Client);

impl GoodsDetector {
    fn new() -> GoodsDetector {
        GoodsDetector(reqwest::ClientBuilder::new()
            .danger_accept_invalid_certs(true)
            .danger_accept_invalid_hostnames(true)
            .timeout(std::time::Duration::from_secs(10))
            .gzip(true)
            .build()
            .unwrap()
        )
    }

    fn get(&self, url: &str) -> String {
        loop {
            match self.0.get(url).send() {
                Ok(mut resp) => return resp.text().unwrap(),
                Err(e) => println!("{:?}", e),
            }
        }
    }

    fn is_on_sale(&self, url: &str) -> bool { self.get(url).contains("点击此按钮，到下一步确认购买信息") }
}

fn main() {
    // --- std ---
    use std::{
        fs::File,
        io::Write,
    };
    // --- external ---
    use calamine::{Xlsx, Reader};
    use url::Url;

    let goods_detector = GoodsDetector::new();
    let mut pull_off_shelves = String::new();
    let mut excel: Xlsx<_> = {
        let path = {
            // --- std ---
            use std::io::{
                stdin,
                stdout,
            };

            let mut s = String::new();

            print!("Path -> ");
            stdout().flush().unwrap();
            stdin().read_line(&mut s).unwrap();

            s.trim().to_owned()
        };

        calamine::open_workbook(path).unwrap()
    };
    for row in excel.worksheet_range("Sheet1")
        .unwrap()
        .unwrap()
        .rows() {
        let id = row[1].get_string().unwrap();
        let url = row[2].get_string().unwrap();

        let info = format!("id: {}, url: {}", id, url);
        println!("{}", info);

        if Url::parse(url).is_err() || !goods_detector.is_on_sale(url) {
            pull_off_shelves.push_str(&info);
            pull_off_shelves.push('\n');
        }
    }

    let mut f = File::create("pull_off_shelves.txt").unwrap();
    f.write_all(pull_off_shelves.as_bytes()).unwrap();
    f.sync_all().unwrap();
}
