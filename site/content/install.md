# Install

A skill is a directory of markdown. Clone the repo and copy all eight into
your agent's skills folder:

```
git clone https://github.com/0trm/gallop
mkdir -p .claude/skills
cp -r gallop/skills/* .claude/skills/
```

Or copy one, by its name on [the skills page](../skills/):

```
cp -r gallop/skills/reading-experiments .claude/skills/
```

Works with anything that reads Agent Skills, and reads fine as prose:
each `SKILL.md` is the procedure, the `reference/` files one level down are
the depth.
