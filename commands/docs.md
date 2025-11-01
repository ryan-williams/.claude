Review and update documentation files in the project.

If the user provided additional paths or hints after `/docs`, focus on those specific areas.
Otherwise, look for documentation broadly (`.md` files, `docs/` directories, `README` files, etc.).

Steps:
1. Determine the scope:
   - If specific paths/hints provided: focus on those areas
   - Otherwise: search for documentation files using `find . -name "*.md" -type f` and check for `docs/` directories
2. Read the relevant documentation files
3. Review the current codebase to understand:
   - Recent changes that might need documentation updates
   - Features/APIs that are documented
   - Any mismatches between code and docs
4. Identify documentation issues:
   - Outdated information
   - Missing documentation for new features
   - Unclear or incomplete explanations
   - Broken examples or code snippets
   - Inconsistent formatting
5. Propose updates or ask the user which issues to address
6. Make the documentation updates using the Edit tool
7. Summarize what was updated

Important:
- Read existing docs carefully before making changes
- Maintain the existing tone and style of the documentation
- Ensure code examples are accurate and runnable
- Update version numbers, dates, or other metadata as appropriate
- Don't remove useful information without good reason
- If uncertain about a change, ask the user first
