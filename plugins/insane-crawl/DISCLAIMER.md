# Disclaimer & acceptable use — insane-crawl

`insane-crawl` is MIT-licensed software provided **AS IS**, without warranty.
It is a local developer tool for lawful, authorized collection of publicly
available pages. The user is solely responsible for compliance with applicable
law, website terms, robots rules, rate limits, and content-use signals.

The tool does not log in, defeat paywalls, solve CAPTCHAs, buy access, rotate
identities to evade a refusal, or make private endpoints public. It stops or
records a partial result when public access is unavailable. An explicit
`--ignore-robots` option exists for targets the user owns or is authorized to
test; using it does not grant authorization and is recorded in the job receipt.

Endpoint discovery is not enabled in the MVP. Future discovery must only
consider requests actually observed from the user-supplied public page in that
run, keep a separate budget, and prove attribution before any automated fast
path can use a recipe.
