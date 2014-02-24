<#
.Synopsis
Determines if the system is a Read-Write Domain Controller, Read-Only Domain Controller or not a Domain Controller at all.
.DESCRIPTION
Determines if the system is a Read-Write Domain Controller, Read-Only Domain Controller or not a Domain Controller at all.
.EXAMPLE
PS C:\> Get-DomainType -Computername <ComputerName/FQDN/IP Address> -Credential $Credential
The following server is a Read-Only Domain Controller.
The main Read-Write Domain Controller can be found at SC-AD1.seccom.test.

PS C:\> Get-DomainType
This machine is not a Domain Controller.
#>

function Get-DCType
{
    [CmdletBinding()]
    [OutputType([byte])]
    Param
    (
		[parameter(ValueFromPipeline=$true,
		ValueFromPipelineByPropertyName=$true)]
		[string]$Computername="$env:COMPUTERNAME",

		[Parameter(Mandatory=$false)]
		[System.Management.Automation.PSCredential]
		[System.Management.Automation.Credential()]$Credential = [System.Management.Automation.PSCredential]::Empty
    )

    Begin
    {
		$reg = Get-WmiObject -List "StdRegprov" -ComputerName $computername -Credential $Credential
	}
	
    Process
    {
       
        $reg_hive = 2147483650
		$dc_key = "SYSTEM\\CurrentControlSet\\Services\\NTDS"
		$dc_sname = "Parameters"
		$rodc_key = "SYSTEM\\CurrentControlSet\\Services\\NTDS\\Parameters"
		$rodc_sname = "Src Root Domain Srv"
		
		$is_dc = $false
		$is_rodc = $false
		
        $data = $reg.EnumKey($reg_hive, $dc_key)
        if ($data.ReturnValue -eq 0)
        {
            if ($data.snames -contains $dc_sname)
            {
				$is_dc = $true
				$valdata = $reg.EnumValues($reg_hive, $rodc_key)
				if ($valdata.ReturnValue -eq 0)
				{
					if ($valdata.snames -contains $rodc_sname)
					{
						$is_rodc = $true
						$rwdc_fqdn = ($reg.GetStringValue($reg_hive, $rodc_key, $rodc_sname)).svalue
					}
				}
			}
		}
		
		if ($is_rodc)
		{
		#	Write-Verbose "The following server is a Read-Only Domain Controller."
		#	Write-Verbose "The main Read-Write Domain Controller can be found at $rwdc_fwdn."
			Write-Host "The following server is a Read-Only Domain Controller."
			Write-Host "The main Read-Write Domain Controller can be found at $rwdc_fqdn."
		}
		elseif ($is_dc)
		{
		#	Write-Verbose "The following server is a Read-Write Domain Controller."
			Write-Host "The following server is a Read-Write Domain Controller."
		}
		else
		{
		#	Write-Verbose "This machine is not a Domain Controller."
			Write-Host "This machine is not a Domain Controller."
		}
    }
    End
    {
    }
}