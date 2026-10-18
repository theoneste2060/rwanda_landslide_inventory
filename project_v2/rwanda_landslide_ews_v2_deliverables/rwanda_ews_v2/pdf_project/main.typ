// Markdown adapter entry.
// Prepared projects receive report-theme.typ beside this file.

#import "@preview/cmarker:0.1.10"
#import "@preview/mitex:0.2.7": mitex
#import "report-theme.typ": report-theme

#let markdown-source = "source.md"

#show: report-theme.with(
  first-line-indent: none,
  running-header: false,
)

// cmarker emits tables with all-auto column widths. Re-emit those tables as
// full-width, booktabs-style tables while leaving explicitly sized tables alone.
#show table: it => {
  if it.columns.len() > 0 and it.columns.all(column => column == auto) {
    table(
      columns: (1fr,) * it.columns.len(),
      align: it.align,
      stroke: none,
      inset: (x: 10pt, y: 7pt),
      fill: (_, y) => if y > 0 and calc.even(y) { luma(248) } else { none },
      table.hline(stroke: 1pt),
      ..it.children.filter(
        child => child.func() != table.hline and child.func() != table.vline,
      ),
      table.hline(stroke: 1pt),
    )
  } else {
    it
  }
}
#show table.cell.where(y: 0): set text(weight: "bold")

// mitex renders LaTeX equations found in the Markdown source.
#let markdown-text = read(markdown-source)
#let figure-markdown = "![Synthetic sample-size demonstration: intensity-duration curve uncertainty and held-out AUC variability](outputs/synthetic_sample_size/synthetic_sample_size_demo.png)"
#let markdown-parts = markdown-text.split(figure-markdown)
#assert(markdown-parts.len() == 2, message: "Expected exactly one sample-size figure marker in the Markdown source.")
#cmarker.render(markdown-parts.at(0), math: mitex)
#figure(
  image("outputs/synthetic_sample_size/synthetic_sample_size_demo.png", width: 100%),
  caption: [Synthetic sample-size demonstration: intensity-duration curve uncertainty and held-out AUC variability],
)
#cmarker.render(markdown-parts.at(1), math: mitex)
