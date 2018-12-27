// --- std ---
use std::{
    fs::{self, File},
    io::{self, Read, Write},
    path::{Path, PathBuf},
    thread,
};

type Files = Vec<(PathBuf, String)>;

fn is_target_dir(path: &Path) -> bool {
    let dir_name = path.file_name()
        .unwrap()
        .to_str()
        .unwrap();

    dir_name.ends_with('_') && (dir_name.starts_with("60") || dir_name.starts_with("00"))
}

fn is_target_file(path: &Path, file_name: &str) -> bool {
    if file_name.starts_with("SHL") || file_name.starts_with("SZL1") {
        let file_size = fs::metadata(path).unwrap().len() / 1000;

        if file_size <= 10 {
            println!("File: {}, Size: {} KB, ignored", path.to_str().unwrap(), file_size);
            false
        } else {
            println!("File: {}, Size: {} KB", path.to_str().unwrap(), file_size);
            true
        }
    } else { false }
}

fn get_date(file_name: &str) -> u32 {
    let len = file_name.len();
    file_name[len - 10..len - 4].parse::<u32>().unwrap()
}

fn read_dir(path: &Path) -> Files {
    let mut files: Files = path.read_dir()
        .unwrap()
        .map(|entry| {
            let f = entry.unwrap();
            (f.path().to_owned(), f.file_name().to_str().unwrap().to_owned())
        })
        .filter(|(path, file_name)| is_target_file(path, file_name))
        .collect();
    files.sort_by_key(|(_, file_name)| get_date(file_name));

    files
}

fn concat_txt(files: Files) {
    for year in files.chunks(12) {
        let mut sum = {
            let (path, file_name) = &year[0];
            let mut path = path.to_owned();
            path.set_file_name(&format!("SUM_{}.txt", &file_name[..file_name.len() - 6]));

            File::create(path).unwrap()
        };

        for (path, _) in year {
            let mut file = File::open(path).unwrap();
            let mut data = vec![];

            file.read_to_end(&mut data).unwrap();
            sum.write_all(&mut data).unwrap();
        }

        sum.sync_all().unwrap();
    }
}

fn main() {
    let path = {
        print!("Specify path: ");
        io::stdout().flush().unwrap();

        let mut s = String::new();
        io::stdin().read_line(&mut s).unwrap();

        s.trim().to_owned()
    };

    if path.is_empty() {
        let mut handles = vec![];
        for entry in Path::read_dir(Path::new(".")).unwrap() {
            let path = entry.unwrap().path();
            if is_target_dir(&path) {
                handles.push(
                    thread::spawn(move || {
                        concat_txt(read_dir(&path));
                        println!("Folder: {}, finished", path.to_str().unwrap());
                    })
                );
            }
        }

        for handle in handles { handle.join().unwrap(); }
    } else { concat_txt(read_dir(&Path::new(&path))); }

    println!("Finished, press Enter to exit");
    let mut s = String::new();
    io::stdin().read_line(&mut s).unwrap();
}
