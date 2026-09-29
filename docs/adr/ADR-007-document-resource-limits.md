# ADR-007: DOCX Resource Limits

Status: Accepted for M2 carry-over  
Date: 2026-09-29

DOCX input is an untrusted ZIP/XML container. `DocxResourceLimits` configures compressed archive
bytes, member count, total uncompressed bytes, individual member bytes, XML part bytes,
relationship count, and parsed XML depth. Defaults are project safety policy, not format facts.
Callers can lower them for services or raise them explicitly for known local material.

Limits are checked before reading high-risk members; XML depth is checked after the standard
library parser builds a bounded-size tree. No macros or embedded objects execute. This closes
trivial ZIP bomb and deep/oversized document paths but is not a complete sandbox: CPU-time,
compression-ratio, memory, and hostile native-library risks still require process isolation in
service deployments.

