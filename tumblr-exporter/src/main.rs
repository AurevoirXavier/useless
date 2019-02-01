extern crate regex;
extern crate reqwest;
extern crate rumblr;
extern crate serde_json;

// --- external ---
use regex::Regex;
use rumblr::{TumblrClient, GetBlogPostsOptionalParams};
use serde_json::Value;

fn main() {
    let client = TumblrClient::new()
        .proxy("http://127.0.0.1:1087")
        .unwrap()
        .load_keys("rumblr.keys")
        .unwrap();

    let limit = 10;
    for i in 0u32.. {
        let resp: Value = client.get_blog_posts(
            "smsp520.tumblr.com",
            Some(GetBlogPostsOptionalParams::new()
                .limit(&limit.to_string())
                .offset(&(i * limit).to_string())),
        );

        println!("{:#?}", resp);

//        let re = Regex::new(r#"<a href="(.+?)">"#).unwrap();
//        let path = "export";
//        {
//            // --- std ---
//            use std::{
//                fs::create_dir,
//                path::Path,
//            };
//
//            let path = Path::new(path);
//            if !path.is_dir() { create_dir(path).unwrap(); }
//        }
//
        let posts = resp["response"]["posts"].as_array().unwrap();
//        for post in posts {
//            let mut infos = String::new();
//
//            {
//                let trail = post["trail"].as_array().unwrap();
//                if !trail.is_empty() {
//                    let content_raw = trail[0]["content_raw"].as_str().unwrap();
//                    for cap in re.captures_iter(content_raw) {
//                        if let Some(download_link) = cap.get(1) {
//                            infos.push_str(&format!("Download link: {}", download_link.as_str()));
//                            infos.push('\n');
//                        }
//                    }
//                }
//            }
//
//            {
//                let photos = post["photos"].as_array().unwrap();
//                for photo in photos {
//                    infos.push_str(&format!("Preview: {}", photo["original_size"]["url"].as_str().unwrap()));
//                    infos.push('\n');
//                }
//            }
//
//            {
//                // --- std ---
//                use std::{
//                    fs::File,
//                    io::Write,
//                };
//
//                let mut f = File::create(&format!("{}/{}.txt", path, post["id"].as_u64().unwrap())).unwrap();
//                f.write_all(infos.as_bytes()).unwrap();
//                f.sync_all().unwrap();
//            }
//        }

        if posts.len() != limit as usize { break; }
    }
}
