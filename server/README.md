<!--
SPDX-FileCopyrightText: 2026 Matheus Tagliari and BWR-1 contributors
SPDX-License-Identifier: AGPL-3.0-or-later
-->
# BWR-1 network services

This directory is reserved for software that serves BWR-1 data to other people over a network: the data/archive server, PPI and web publishing, and APIs (including the Beackman/Chuvalski integration endpoint).

Everything here is licensed under **AGPL-3.0-or-later**. If you run a modified version of this software and let other people interact with it over a network, you must offer those users the corresponding source code of your modified version (AGPL-3.0, section 13).

Radar-side code that does not serve users over a network (firmware, acquisition, DSP, tools) belongs in `firmware/` or `software/` under GPL-3.0-or-later. See [LICENSING.md](../LICENSING.md).
