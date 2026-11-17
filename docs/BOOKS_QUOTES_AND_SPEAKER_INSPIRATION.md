# Books, quotations and speaker inspiration policy

The Finance Campus may draw on classical financial books, respected financial educators, behavioural thinkers, entrepreneurs and public speakers. Their ideas should deepen a mindset lesson without turning a script into a quote compilation.

## Preferred order of use

1. **Verified paraphrase:** independently explain the author's idea in original language, attribute the idea and identify the original work.
2. **Public-domain text:** quote only after checking the work and the relevant edition, translation and territory.
3. **Permission or compatible licence:** retain evidence of the permission/licence and comply with its conditions.
4. **Copyrighted direct quotation:** do not use by default. Escalate for rights review; attribution and brevity alone do not guarantee permission or a legal exception.

## Script data contract

An optional `inspiration` object may be included in a topic record:

```json
{
  "kind": "paraphrase",
  "author": "Author name",
  "work": "Verified book or speech title",
  "source_url": "https://example.org/original-source",
  "text": "An independently written summary of the idea, not a close rewrite of the original passage.",
  "verification": "author_and_original_work_verified",
  "original_wording_reused": false
}
```

For a direct quotation, use `kind: direct_quote`, include the exact words, and additionally set:

- `rights_basis`: `public_domain`, `permission_granted` or `compatible_license`;
- `rights_verified`: `true` only after a human has checked rights for the intended use and territory.

The generator rejects direct quotes without those rights fields and rejects quotations longer than 15 words. The 15-word limit is an internal editorial safeguard, not a legal safe harbour. Automated checks cannot determine copyright status or establish whether a use is fair dealing/fair use.

## Editorial and research checks

- Check the author against the original work or a trustworthy publisher, archive, institutional or primary source.
- Confirm the wording before using quotation marks. If wording cannot be confirmed, paraphrase the idea without quotation marks or omit it.
- Record the original work and source URL. Do not rely solely on quote aggregators, social posts or AI-generated attributions.
- Avoid overusing one speaker. Use ideas from a range of relevant traditions and perspectives.
- Do not imply that an author's fame proves a financial claim. Verify factual claims independently with reputable sources.
- Preserve context. Do not turn a nuanced statement into a universal financial rule or promise.
- A paraphrase must be genuinely original expression. Changing a few words while retaining a distinctive sentence structure is not enough.
- Rights and exceptions vary by jurisdiction. If there is doubt, leave the direct quote out and use a carefully attributed paraphrase instead.

## Example: using a modern speaker

For a modern speaker such as Zig Ziglar, the default is not to reproduce a famous line verbatim. Find the original book or talk, verify the idea, then explain it in our own words and attribute the idea to that work. The script should then connect the lesson to a relatable money decision and a practical action.
