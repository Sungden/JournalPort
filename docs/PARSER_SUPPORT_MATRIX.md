# Parser Support Matrix

Statuses are exact M1 claims. `PARTIAL` means represented with preserved evidence and documented
limits; it never implies submission readiness.

| Feature | DOCX status | LaTeX status | Canonical representation | Lossless? | Blocking? | Notes |
|---|---|---|---|---|---|---|
| title | SUPPORTED | SUPPORTED | metadata.title | Yes for detected source | No | DOCX style/core metadata; LaTeX `title` |
| authors | PARTIAL | PARTIAL | metadata.authors | Raw text retained | No | Complex affiliations not interpreted |
| affiliations | PARTIAL | PARTIAL | metadata.affiliations | No | No | Detection deferred beyond basic metadata |
| abstract | PARTIAL | SUPPORTED | section tree | Text-preserving | No | DOCX requires recognizable heading/style |
| headings | SUPPORTED | SUPPORTED | sections/subsections | Yes in subset | No | DOCX Heading styles; LaTeX section commands |
| paragraphs | SUPPORTED | PARTIAL | TextBlock | Yes in subset | Unknown macros block | LaTeX scanner retains command text |
| bold/italic | UNSUPPORTED_NONCRITICAL | UNSUPPORTED_NONCRITICAL | plain text | Text only | No | Formatting is not modeled in M1 |
| lists | PARTIAL | PARTIAL | paragraphs/raw commands | Text-preserving | No | List semantics not normalized |
| tables | PARTIAL | PARTIAL | Asset | Raw/hash preserved | No | Cell semantics/LaTeX tabular AST deferred |
| figures | PARTIAL | PARTIAL | Asset | Asset hash/path | Missing asset blocks | Placement semantics deferred |
| captions | PARTIAL | SUPPORTED | Asset.legend | Text-preserving | No | DOCX caption style/lexical detection |
| citations | PARTIAL | SUPPORTED | Citation | Raw + keys | Unknown form blocks | DOCX field citations only |
| bibliography | PARTIAL | PARTIAL | Reference | Raw entries | External DB warning | `bibitem` supported; `.bib` deferred |
| inline equations | PARTIAL | SUPPORTED | Equation/raw evidence | Raw form preserved | No | Common `$...$` and `\\(...\\)` forms |
| display equations | SUPPORTED | SUPPORTED | Equation | Raw OMML/LaTeX | No | Conversion intentionally deferred |
| equation numbers | PARTIAL | PARTIAL | Equation.label/raw | Raw-preserved | No | Number resolution deferred |
| footnotes | PARTIAL | PARTIAL | Note/raw paragraph | DOCX part preserved | Unknown complex macros block | LaTeX `footnote` remains raw command |
| endnotes | PARTIAL | NOT_APPLICABLE | Note | DOCX part preserved | No | LaTeX package-specific endnotes unknown |
| cross-references | PARTIAL | PARTIAL | raw fields/refs | Raw-preserved | Unknown field may block | Resolution deferred |
| hyperlinks | PARTIAL | PARTIAL | text/raw command | Raw-preserved | No | Targets not normalized |
| tracked changes | UNSUPPORTED_BLOCKING | NOT_APPLICABLE | UnsupportedContent | Both raw XML views | Yes | Never selects final/original silently |
| comments | UNSUPPORTED_BLOCKING | UNSUPPORTED_NONCRITICAL | UnsupportedContent/raw source | Partial | DOCX yes | Comment relationship mapping deferred |
| fields | PARTIAL | NOT_APPLICABLE | Citation/UnsupportedContent | Instruction preserved | Unknown scientific field | REF/SEQ/HYPERLINK recognized |
| OMML | SUPPORTED | NOT_APPLICABLE | Equation(OMML) | Raw XML | No | Semantic conversion deferred |
| embedded objects | UNSUPPORTED_BLOCKING | NOT_APPLICABLE | UnsupportedContent | Raw XML | Yes | May contain scientific content |
| floating shapes | UNSUPPORTED_BLOCKING | NOT_APPLICABLE | UnsupportedContent | Partial | Yes | Layout/content extraction deferred |
| text boxes | UNSUPPORTED_BLOCKING | NOT_APPLICABLE | UnsupportedContent | Raw XML | Yes | Avoid silent off-flow text loss |
| supplementary references | PARTIAL | PARTIAL | Asset/Reference | Raw-preserved | No | Semantics deferred |
| custom LaTeX macros | NOT_APPLICABLE | UNSUPPORTED_BLOCKING | UnsupportedContent | Command preserved | Yes | No arbitrary expansion |
| input/include | NOT_APPLICABLE | SUPPORTED | per-object SourceLocator | Yes in safe subset | Unsafe/missing/cycle | Root-confined and cycle-detected |
| custom environments | NOT_APPLICABLE | UNSUPPORTED_BLOCKING | UnsupportedContent | Raw source | Yes | Known subset only |

