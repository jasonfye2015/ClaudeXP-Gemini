// Claude Timeline.exe: one click to the SYSTEC Multi-Boot Manager, on any Windows 10/11 PC, straight from the SSD.
// It does what "Claude Timeline.bat" does, without a console window: run ClaudeLauncher\main.py with the Timeline's own
// portable Python (Python\pythonw.exe), or ClaudeXP's .venv on the development PC, never the PC's own Python.
// Built by build.bat with the C# compiler every Windows has (.NET Framework 4).
using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("Claude Timeline")]
[assembly: System.Reflection.AssemblyProduct("Claude Timeline - SYSTEC Multi-Boot Manager")]
[assembly: System.Reflection.AssemblyVersion("1.0.0.0")]

static class ClaudeTimeline
{
    [STAThread]
    static int Main()
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string script = Path.Combine(root, "ClaudeLauncher", "main.py");
        string[] pythons = {
            Path.Combine(root, "Python", "pythonw.exe"),
            Path.Combine(root, "ClaudeXP", ".venv", "Scripts", "pythonw.exe"),
        };
        string python = null;
        foreach (string p in pythons)
            if (File.Exists(p)) { python = p; break; }
        if (python == null || !File.Exists(script))
        {
            MessageBox.Show("Claude Timeline can't start: " + (python == null
                ? "the Timeline's Python (the Python folder beside this program) is missing."
                : "ClaudeLauncher\\main.py is missing.") + "\n\nThis program has to sit in the Claude Timeline folder.",
                "Claude Timeline", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
        var start = new ProcessStartInfo(python, "\"" + script + "\"");
        start.UseShellExecute = false;
        start.WorkingDirectory = root;
        start.EnvironmentVariables["PYTHONNOUSERSITE"] = "1";      // only the Timeline's own packages
        try
        {
            Process.Start(start);
        }
        catch (Exception e)
        {
            MessageBox.Show("Claude Timeline can't start:\n\n" + e.Message, "Claude Timeline",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
        return 0;
    }
}
