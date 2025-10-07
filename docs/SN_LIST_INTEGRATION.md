# SN List Integration to Config.toml

## Summary

Successfully integrated the sn_list functionality into the config.toml system, eliminating the need for a separate sn_list.txt file.

## Changes Made

### 1. Schema Updates ([schema.py](schema.py))

- Added `sn_list: str = ""` field to `Config` dataclass (line 144)
- Added `sn_list: str` field to `Settings` dataclass (line 240)

### 2. Config Module Updates ([config.py](config.py))

#### New Helper Function
- **`_parse_sn_list_text()`** (line 357): Parses sn_list text content into dictionary format
  - Supports tags (@tag_name)
  - Supports download modes (latest/all/largest-sn)
  - Supports custom bangumi names (<custom_name>)
  - Supports comments (#)

#### Updated Functions
- **`read_sn_list()`** (line 403):
  - Now reads from config.toml instead of sn_list.txt
  - Automatically migrates existing sn_list.txt files
  - Creates backup (.txt.bak) after migration
  - Returns parsed dictionary format

- **`get_sn_list_content()`** (line 93):
  - Returns raw sn_list string from config.toml
  - Used by Web dashboard

- **`write_sn_list()`** (line 665):
  - Saves sn_list content to config.toml
  - Properly updates Config object

- **`get_settings()`** (line 304):
  - Added sn_list to Settings construction

### 3. Dashboard Updates ([dashboard/server.py](dashboard/server.py))

- **`update_sn_list()`** endpoint (line 457):
  - Added `config.invalidate_settings_cache()` call
  - Ensures settings cache is refreshed after sn_list updates

### 4. Sample Config Updates ([config-sample.toml](config-sample.toml))

- Added sn_list section with documentation (line 117-130)
- Included format examples:
  - Single SN: `12345`
  - With download mode: `12345 latest`
  - With custom name: `12345 <自定義名稱>`
  - With tag: `@本季新番`
  - With comments: `# 注釋內容`

## Migration Behavior

### Automatic Migration
When `read_sn_list()` is called:
1. Checks for `sn_list.txt.txt` (防呆) and renames to `sn_list.txt`
2. If config.sn_list is empty AND sn_list.txt exists:
   - Reads sn_list.txt content
   - Saves to config.toml
   - Creates backup (sn_list.txt.bak)
   - Removes original sn_list.txt
   - Prints migration message

### Data Format
- **Storage**: Plain text in config.toml (preserves original format including comments and tags)
- **Runtime**: Parsed dictionary with structure:
  ```python
  {
      sn_number: {
          'mode': str,      # 'latest', 'all', or 'largest-sn'
          'tag': str,       # Category tag (from @tag)
          'rename': str     # Custom bangumi name (from <name>)
      }
  }
  ```

## Testing Results

### Test 1: Migration
```bash
$ uv run python -c "import config; sn = config.read_sn_list(); print('SN List:', sn)"
已將 sn_list.txt 遷移到 config.toml，舊檔案已備份到 /home/sheildon/aniGamerPlus/sn_list.txt.bak
SN List: {45584: {'mode': 'latest', 'tag': '', 'rename': ''}}
```
✓ Migration successful

### Test 2: Write and Read
```bash
$ uv run python -c "config.write_sn_list(test_content); sn = config.read_sn_list()"
讀取結果: {
    12345: {'mode': 'latest', 'tag': '本季新番', 'rename': '測試番劇'},
    12346: {'mode': 'all', 'tag': '本季新番', 'rename': ''},
    12347: {'mode': 'latest', 'tag': '舊番', 'rename': ''}
}
```
✓ Write and read successful

### Test 3: Type Checking
```bash
$ uv run ty check
✓ No type errors - only warnings remain
```
✓ Type checking passed

## Backwards Compatibility

- Existing sn_list.txt files are automatically migrated on first read
- Backup files are created to prevent data loss
- No manual intervention required
- Dashboard API endpoints remain unchanged

## Benefits

1. **Unified Configuration**: All settings in one file (config.toml)
2. **Type Safety**: Validated through Config dataclass
3. **Automatic Migration**: Seamless upgrade path
4. **Data Preservation**: Original format preserved (comments, tags, etc.)
5. **Cache Management**: Proper invalidation on updates
