use kuromoji_wasm::tokenize_native;

#[test]
fn check_detail_indices() {
    // Print all details for 食べました so we can verify IPAdic indices
    let tokens = tokenize_native("食べました");
    for t in &tokens {
        println!("surface: {}", t.surface_form);
        println!("  reading={} basic_form={} pos={} pos_detail_1={}", t.reading, t.basic_form, t.pos, t.pos_detail_1);
    }
}

#[test]
fn basic_verb_conjugation() {
    let tokens = tokenize_native("食べました");
    let t = tokens.iter().find(|t| t.surface_form == "食べ").unwrap();
    assert_eq!(t.basic_form, "食べる", "basic_form for 食べ");
    assert_eq!(t.pos, "動詞", "pos for 食べ");
}

#[test]
fn particle_ha() {
    let tokens = tokenize_native("私は");
    let t = tokens.iter().find(|t| t.surface_form == "は").unwrap();
    assert_eq!(t.pos, "助詞", "pos for は");
}

#[test]
fn conjunctive_particle_te() {
    let tokens = tokenize_native("食べて");
    let t = tokens.iter().find(|t| t.surface_form == "て").unwrap();
    assert_eq!(t.pos, "助詞", "pos for て");
    assert_eq!(t.pos_detail_1, "接続助詞", "pos_detail_1 for て");
}

#[test]
fn auxiliary_desu() {
    let tokens = tokenize_native("です");
    let t = &tokens[0];
    assert_eq!(t.pos, "助動詞", "pos for です");
}

#[test]
fn godan_imperative_harae() {
    let tokens = tokenize_native("払え");
    let t = &tokens[0];
    println!("払え -> basic_form: {}, pos: {}", t.basic_form, t.pos);
    // Document whatever Lindera returns — both 払う (correct) and 払える (kuromoji compat) work with app
}

#[test]
fn shine_interjection() {
    let tokens = tokenize_native("死ね");
    let t = &tokens[0];
    println!("死ね -> basic_form: {}, pos: {}", t.basic_form, t.pos);
}

#[test]
fn katakana_reading_returned() {
    let tokens = tokenize_native("日本語");
    let t = tokens.iter().find(|t| t.surface_form == "日本語").unwrap();
    assert!(
        t.reading.chars().all(|c| (c >= '\u{30A0}' && c <= '\u{30FF}') || c == '*'),
        "reading should be katakana, got: {}",
        t.reading
    );
}

#[test]
fn unknown_word() {
    let tokens = tokenize_native("ナントカカントカ");
    assert!(!tokens.is_empty(), "unknown word should produce at least one token");
}

#[test]
fn grammar_dimming_pos_strings() {
    // Verify that Lindera uses exactly the Japanese POS strings the app expects for dimming
    let cases = vec![
        ("は", "助詞"),
        ("です", "助動詞"),
    ];
    for (word, expected_pos) in cases {
        let tokens = tokenize_native(word);
        let t = tokens.iter().find(|t| t.surface_form == word).unwrap();
        assert_eq!(t.pos, expected_pos, "pos for {}", word);
    }
}
