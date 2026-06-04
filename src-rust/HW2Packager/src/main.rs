use std::env;
use std::fs::{self, File};
use std::collections::HashSet;
use std::io::{self, BufRead, BufReader, BufWriter, Write};
use std::path::{Path, PathBuf};

const SIGNATURE: &[u8; 6] = b"capack";
const VERSION_USES_ALIGNMENT: u64 = 2;
const DEFAULT_ALIGNMENT: u64 = 8;
const COPY_BUFFER_SIZE: usize = 8 * 1024 * 1024;

#[derive(Debug)]
struct Entry {
    package_name: String,
    file_path: PathBuf,
    size: u64,
    offset: u64,
}

fn print_usage() {
    eprintln!("HW2 PKG Packager 0.1");
    eprintln!("Usage:");
    eprintln!("  hw2pkg package <INPUT_FOLDER> -o <OUTPUT.pkg> [--embed-streaming-videos] [--include-loose-xml]");
    eprintln!("  hw2pkg <INPUT_FOLDER> -o <OUTPUT.pkg> [--embed-streaming-videos] [--include-loose-xml]");
    eprintln!();
    eprintln!("By default, .bk2/.bik files are written to <OUTPUT>_loose instead of embedded.");
    eprintln!("By default, loose editable .xml files are skipped when compiled .xml.xmb files are present.");
}

fn parse_args() -> Result<(PathBuf, PathBuf, bool, bool), String> {
    let mut args: Vec<String> = env::args().skip(1).collect();
    if args
        .first()
        .map(|value| value.eq_ignore_ascii_case("package"))
        .unwrap_or(false)
    {
        args.remove(0);
    }

    if args.iter().any(|arg| arg == "-h" || arg == "--help") {
        print_usage();
        std::process::exit(0);
    }

    let mut input: Option<PathBuf> = None;
    let mut output: Option<PathBuf> = None;
    let mut split_streaming_videos = true;
    let mut include_loose_xml = false;
    let mut index = 0;
    while index < args.len() {
        match args[index].as_str() {
            "-o" | "--output" => {
                index += 1;
                let value = args.get(index).ok_or("Missing output path after -o")?;
                output = Some(PathBuf::from(value));
            }
            "--embed-streaming-videos" => {
                split_streaming_videos = false;
            }
            "--include-loose-xml" => {
                include_loose_xml = true;
            }
            value if value.starts_with('-') => {
                return Err(format!("Unknown option: {value}"));
            }
            value => {
                if input.is_some() {
                    return Err(format!("Unexpected extra input: {value}"));
                }
                input = Some(PathBuf::from(value));
            }
        }
        index += 1;
    }

    let input = input.ok_or("Missing input folder")?;
    let output = output.unwrap_or_else(|| PathBuf::from("out.pkg"));
    Ok((input, output, split_streaming_videos, include_loose_xml))
}

fn ascii_package_name(package_root: &Path, file_path: &Path) -> Result<String, String> {
    let relative = file_path
        .strip_prefix(package_root)
        .map_err(|error| format!("Could not make relative path for {}: {error}", file_path.display()))?;

    let normalized = relative
        .components()
        .map(|component| component.as_os_str().to_string_lossy())
        .collect::<Vec<_>>()
        .join("\\");
    let package_name = format!("\\{normalized}");
    if !package_name.is_ascii() {
        return Err(format!("Package path is not ASCII: {package_name}"));
    }
    Ok(package_name)
}

fn normalize_manifest_line(value: &str) -> Option<String> {
    let trimmed = value.trim().trim_start_matches('\u{feff}');
    if trimmed.is_empty() || trimmed.starts_with('#') || trimmed.starts_with("//") {
        return None;
    }
    if trimmed.eq_ignore_ascii_case("v2") {
        return None;
    }

    let normalized = trimmed
        .trim_start_matches('\\')
        .trim_start_matches('/')
        .replace('/', "\\");
    if normalized.is_empty() {
        None
    } else {
        Some(normalized.to_ascii_lowercase())
    }
}

fn manifest_filter(root: &Path) -> Result<Option<HashSet<String>>, String> {
    let manifest_path = root.join("file_manifest.txt");
    if !manifest_path.is_file() {
        return Ok(None);
    }

    let file = File::open(&manifest_path)
        .map_err(|error| format!("Could not open {}: {error}", manifest_path.display()))?;
    let mut allowed = HashSet::new();
    for line in BufReader::new(file).lines() {
        let line = line.map_err(|error| format!("Could not read {}: {error}", manifest_path.display()))?;
        if let Some(path) = normalize_manifest_line(&line) {
            allowed.insert(path.clone());
            allowed.insert(format!("data\\{path}"));
            if path.ends_with(".xml") || path.ends_with(".pfx") || path.ends_with(".tactics") {
                let compiled = format!("{path}.xmb");
                allowed.insert(compiled.clone());
                allowed.insert(format!("data\\{compiled}"));
            }
        }
    }
    Ok(Some(allowed))
}

fn is_loose_editable_xml(file_path: &Path) -> bool {
    file_path
        .extension()
        .and_then(|extension| extension.to_str())
        .map(|extension| extension.eq_ignore_ascii_case("xml"))
        .unwrap_or(false)
}

fn should_include_file(
    package_root: &Path,
    file_path: &Path,
    manifest: Option<&HashSet<String>>,
    include_loose_xml: bool,
) -> Result<bool, String> {
    let relative = file_path
        .strip_prefix(package_root)
        .map_err(|error| format!("Could not make relative path for {}: {error}", file_path.display()))?;
    let normalized = relative
        .components()
        .map(|component| component.as_os_str().to_string_lossy())
        .collect::<Vec<_>>()
        .join("\\")
        .to_ascii_lowercase();

    if !include_loose_xml && is_loose_editable_xml(file_path) {
        return Ok(false);
    }

    if let Some(allowed) = manifest {
        return Ok(allowed.contains(&normalized));
    }

    if normalized == "file_manifest.txt" {
        return Ok(manifest.is_some());
    }

    if normalized == "data.pkg"
        || normalized == "workspace.code-workspace"
        || normalized.ends_with(".code-workspace")
        || normalized.starts_with("_tmp")
    {
        return Ok(false);
    }

    Ok(normalized.starts_with("data\\"))
}

fn is_streaming_video(file_path: &Path) -> bool {
    matches!(
        file_path
            .extension()
            .and_then(|extension| extension.to_str())
            .map(|extension| extension.to_ascii_lowercase())
            .as_deref(),
        Some("bk2") | Some("bik")
    )
}

fn loose_output_root(output_path: &Path) -> PathBuf {
    let stem = output_path
        .file_stem()
        .and_then(|value| value.to_str())
        .unwrap_or("package");
    let folder_name = format!("{stem}_loose");
    output_path
        .parent()
        .map(|parent| parent.join(&folder_name))
        .unwrap_or_else(|| PathBuf::from(folder_name))
}

fn copy_streaming_sidecars(output_path: &Path, streaming_files: &[Entry]) -> Result<(), String> {
    if streaming_files.is_empty() {
        return Ok(());
    }

    let loose_root = loose_output_root(output_path);
    for entry in streaming_files {
        let relative = entry.package_name.trim_start_matches('\\');
        let destination = relative
            .split('\\')
            .fold(loose_root.clone(), |path, part| path.join(part));
        if let Some(parent) = destination.parent() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("Could not create loose video folder {}: {error}", parent.display()))?;
        }
        fs::copy(&entry.file_path, &destination).map_err(|error| {
            format!(
                "Could not copy loose streaming video {} to {}: {error}",
                entry.file_path.display(),
                destination.display()
            )
        })?;
    }
    eprintln!(
        "notice: wrote {} streaming video file(s) to {}. Deploy these loose files with the package; Halo Wars 2 crashes when frontend videos are embedded in capack.",
        streaming_files.len(),
        loose_root.display()
    );
    Ok(())
}

fn collect_files(
    root: &Path,
    output_path: &Path,
    split_streaming_videos: bool,
    include_loose_xml: bool,
) -> Result<(Vec<Entry>, Vec<Entry>), String> {
    if !root.is_dir() {
        return Err(format!("Input is not a folder: {}", root.display()));
    }

    let root = fs::canonicalize(root).map_err(|error| format!("Could not resolve input folder: {error}"))?;
    let manifest = manifest_filter(&root)?;
    let package_root = root.clone();
    let output_canonical = output_path.parent().and_then(|parent| {
        fs::canonicalize(parent)
            .ok()
            .map(|resolved_parent| resolved_parent.join(output_path.file_name().unwrap_or_default()))
    });

    let mut stack = vec![package_root.clone()];
    let mut files: Vec<Entry> = Vec::new();
    let mut streaming_files: Vec<Entry> = Vec::new();
    while let Some(folder) = stack.pop() {
        let read_dir = fs::read_dir(&folder)
            .map_err(|error| format!("Could not read folder {}: {error}", folder.display()))?;
        for item in read_dir {
            let item = item.map_err(|error| format!("Could not read folder item: {error}"))?;
            let path = item.path();
            let metadata = item
                .metadata()
                .map_err(|error| format!("Could not read metadata for {}: {error}", path.display()))?;
            if metadata.is_dir() {
                stack.push(path);
            } else if metadata.is_file() {
                if let Some(output_canonical) = &output_canonical {
                    if &path == output_canonical {
                        continue;
                    }
                }
                if !should_include_file(&package_root, &path, manifest.as_ref(), include_loose_xml)? {
                    continue;
                }
                let entry = Entry {
                    package_name: ascii_package_name(&package_root, &path)?,
                    file_path: path,
                    size: metadata.len(),
                    offset: 0,
                };
                if split_streaming_videos && is_streaming_video(&entry.file_path) {
                    streaming_files.push(entry);
                } else {
                    files.push(entry);
                }
            }
        }
    }

    files.sort_by(|left, right| left.package_name.to_lowercase().cmp(&right.package_name.to_lowercase()));
    streaming_files.sort_by(|left, right| left.package_name.to_lowercase().cmp(&right.package_name.to_lowercase()));
    if files.is_empty() && streaming_files.is_empty() {
        return Err(format!("No files found in {}", root.display()));
    }
    Ok((files, streaming_files))
}

fn entry_serialized_size(entry: &Entry) -> u64 {
    8 + entry.package_name.len() as u64 + 8 + 8
}

fn aligned(value: u64, alignment: u64) -> u64 {
    let remainder = value % alignment;
    if remainder == 0 {
        value
    } else {
        value + (alignment - remainder)
    }
}

fn write_i64<W: Write>(writer: &mut W, value: i64) -> io::Result<()> {
    writer.write_all(&value.to_le_bytes())
}

fn write_u64<W: Write>(writer: &mut W, value: u64) -> io::Result<()> {
    writer.write_all(&value.to_le_bytes())
}

fn build_pkg(input_folder: &Path, output_path: &Path, split_streaming_videos: bool, include_loose_xml: bool) -> Result<usize, String> {
    let (mut entries, streaming_files) = collect_files(input_folder, output_path, split_streaming_videos, include_loose_xml)?;
    copy_streaming_sidecars(output_path, &streaming_files)?;
    if entries.is_empty() {
        return Err("Only streaming video files were found; loose sidecars were written, but a PKG needs at least one non-video file.".to_string());
    }
    let header_size = 6u64 + 8 + 8;
    let entries_size = entries.iter().map(entry_serialized_size).sum::<u64>();
    let first_file_offset = aligned(header_size + entries_size + 8, DEFAULT_ALIGNMENT);

    let mut relative_offset = 0u64;
    for entry in &mut entries {
        relative_offset = aligned(relative_offset, DEFAULT_ALIGNMENT);
        entry.offset = relative_offset;
        relative_offset = relative_offset
            .checked_add(entry.size)
            .ok_or("Package size overflow")?;
    }

    if let Some(parent) = output_path.parent() {
        if !parent.as_os_str().is_empty() {
            fs::create_dir_all(parent)
                .map_err(|error| format!("Could not create output folder {}: {error}", parent.display()))?;
        }
    }

    let output = File::create(output_path)
        .map_err(|error| format!("Could not create {}: {error}", output_path.display()))?;
    let mut writer = BufWriter::with_capacity(COPY_BUFFER_SIZE, output);

    writer
        .write_all(SIGNATURE)
        .map_err(|error| format!("Could not write package signature: {error}"))?;
    write_u64(&mut writer, VERSION_USES_ALIGNMENT)
        .map_err(|error| format!("Could not write package version: {error}"))?;
    write_i64(&mut writer, entries.len() as i64)
        .map_err(|error| format!("Could not write package entry count: {error}"))?;

    for entry in &entries {
        write_i64(&mut writer, entry.package_name.len() as i64)
            .map_err(|error| format!("Could not write name length: {error}"))?;
        writer
            .write_all(entry.package_name.as_bytes())
            .map_err(|error| format!("Could not write package name {}: {error}", entry.package_name))?;
        write_i64(&mut writer, entry.offset as i64)
            .map_err(|error| format!("Could not write file offset: {error}"))?;
        write_i64(&mut writer, entry.size as i64)
            .map_err(|error| format!("Could not write file size: {error}"))?;
    }

    write_u64(&mut writer, DEFAULT_ALIGNMENT)
        .map_err(|error| format!("Could not write alignment: {error}"))?;

    let bytes_written = header_size + entries_size + 8;
    for _ in bytes_written..first_file_offset {
        writer
            .write_all(&[0])
            .map_err(|error| format!("Could not write alignment padding: {error}"))?;
    }

    let mut buffer = vec![0u8; COPY_BUFFER_SIZE];
    let mut current_relative_offset = 0u64;
    for entry in &entries {
        while current_relative_offset < entry.offset {
            writer
                .write_all(&[0])
                .map_err(|error| format!("Could not write file alignment padding: {error}"))?;
            current_relative_offset += 1;
        }
        let mut input = File::open(&entry.file_path)
            .map_err(|error| format!("Could not open {}: {error}", entry.file_path.display()))?;
        loop {
            let read = io::Read::read(&mut input, &mut buffer)
                .map_err(|error| format!("Could not read {}: {error}", entry.file_path.display()))?;
            if read == 0 {
                break;
            }
            writer
                .write_all(&buffer[..read])
                .map_err(|error| format!("Could not write {}: {error}", entry.package_name))?;
            current_relative_offset += read as u64;
        }
    }
    writer
        .flush()
        .map_err(|error| format!("Could not flush {}: {error}", output_path.display()))?;

    Ok(entries.len())
}

fn main() {
    let (input, output, split_streaming_videos, include_loose_xml) = match parse_args() {
        Ok(paths) => paths,
        Err(error) => {
            eprintln!("error: {error}");
            print_usage();
            std::process::exit(2);
        }
    };

    match build_pkg(&input, &output, split_streaming_videos, include_loose_xml) {
        Ok(count) => {
            println!("Packaged {count} file(s) into {}", output.display());
        }
        Err(error) => {
            eprintln!("error: {error}");
            std::process::exit(1);
        }
    }
}
