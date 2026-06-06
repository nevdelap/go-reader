use std::fs::File;
use std::io::Read;
use std::path::PathBuf;

use flate2::read::GzDecoder;
use lindera_core::dictionary_builder::DictionaryBuilder;
use lindera_ipadic_builder::ipadic_builder::IpadicBuilder;
use tar::Archive;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: build-dict <tarball.tar.gz> <output_dir>");
        std::process::exit(1);
    }
    let tarball_path = PathBuf::from(&args[1]);
    let output_dir = PathBuf::from(&args[2]);

    let extract_dir = output_dir.parent().unwrap().join("mecab-ipadic-extract");
    std::fs::create_dir_all(&extract_dir).unwrap();

    println!("Extracting {}...", tarball_path.display());
    let mut tar_gz = File::open(&tarball_path).unwrap();
    let mut buffer = Vec::new();
    tar_gz.read_to_end(&mut buffer).unwrap();
    let decoder = GzDecoder::new(std::io::Cursor::new(buffer));
    let mut archive = Archive::new(decoder);
    archive.unpack(&extract_dir).unwrap();

    let input_dir = extract_dir.join("mecab-ipadic-2.7.0-20070801");

    let tmp_output = output_dir.parent().unwrap().join("lindera-ipadic-tmp");
    let _ = std::fs::remove_dir_all(&tmp_output);

    println!("Building Lindera IPAdic dictionary...");
    IpadicBuilder::new()
        .build_dictionary(&input_dir, &tmp_output)
        .unwrap();

    let _ = std::fs::remove_dir_all(&output_dir);
    std::fs::rename(&tmp_output, &output_dir).unwrap();
    let _ = std::fs::remove_dir_all(&extract_dir);

    println!("Done. Dictionary built at: {}", output_dir.display());
}
