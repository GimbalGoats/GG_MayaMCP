---
summary: "Privacy policy for Maya MCP local server and Claude Desktop extension use."
read_when:
  - When preparing Anthropic directory submission materials.
  - When users or reviewers ask what data Maya MCP collects, stores, or shares.
---

# Privacy Policy

Maya MCP is a local MCP server for controlling Autodesk Maya through Maya's
`commandPort`.

## Data Collection

Maya MCP does not operate a hosted service and does not collect telemetry for
Maya MCP contributors.

The server runs on the user's machine. Tool inputs and outputs are exchanged
between the user's MCP client, the local Maya MCP process, and the user's local
Maya session.

## Data Use

Maya MCP uses tool inputs only to perform the requested local Maya operation.

Examples include:

- reading scene metadata
- listing nodes
- creating or modifying scene objects
- capturing a viewport image
- executing approved scripts from configured local directories

Raw Python or MEL execution through `script.run` is disabled by default and must
be explicitly enabled by the user.

## Data Storage

Maya MCP does not create a central database or hosted account.

Local files may be read or written when the user invokes tools that explicitly
operate on files, such as scene open/save/import/export or viewport capture.

## Data Sharing

Maya MCP contributors do not receive Maya scene data, user files, tool inputs, or
tool outputs from local use of the server.

When used through Claude Desktop or another MCP client, that client may process
tool inputs and outputs as part of normal MCP operation. Review the client's
privacy and data-retention policies for details.

## Retention

Maya MCP does not retain user data centrally.

Any local files, scene changes, client logs, or MCP client conversation records
are controlled by the user, Autodesk Maya, and the MCP client being used.

## Contact

For privacy or security questions, open an issue at:

https://github.com/GimbalGoats/GG_MayaMCP/issues
