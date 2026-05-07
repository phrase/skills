# Phrase Skills

Agent skills for Phrase, following the [Agent Skills](https://agentskills.io) open format.

## Installation

### Claude Code

```bash
claude plugin marketplace add phrase/skills
claude plugin install phrase-skills@phrase-skills
```

Restart Claude Code after installation. Skills activate automatically when relevant.

**Update:**

```bash
claude plugin marketplace update phrase-skills
claude plugin update phrase-skills@phrase-skills
```

Or run `/plugin` to open the plugin manager.

### Codex

```bash
codex plugin marketplace add phrase/skills
```

Run `/plugins` in Codex and toggle `phrase-skills` with Space to enable. Restart Codex. Skills activate automatically when relevant.

**Update:**

```bash
codex plugin marketplace upgrade phrase-skills
```

### Skills Package (skills.sh)

```bash
npx skills add phrase/skills
```

## Available Skills

| Skill | Description |
|-------|-------------|
| [phrase-strings-config](skills/phrase-strings-config/SKILL.md) | Generate a `.phrase.yml` config file for the Phrase CLI and Strings Repo Sync. Detects i18n format and locale file paths. |

### Install individual skill

```bash
npx skills add phrase/skills:<skill>
```

Replace `<skill>` with the skill name from the table above.
