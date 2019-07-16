import os
import paramiko
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import threading
import Queue


def send_mail_attachment(final_str):
    emailfrom = "emailfrom"
    emailtousers = ["recipients email"]
    username = "email"
    password = "password"
    msg = MIMEMultipart()
    msg["From"] = emailfrom
    msg["Subject"] = "Infra Optimization Report"
    msg.preamble = "Infra Optimization Report"
    part1 = MIMEText(final_str, 'html')
    msg.attach(part1)

    server = smtplib.SMTP("SMTP address")
    server.starttls()
    server.login(username, password)
    for emailto in emailtousers:
        msg["To"] = emailto
        server.sendmail(emailfrom, emailto, msg.as_string())
    server.quit()


def total_disk_size(output) :
    tmp_dict = {}
    values_tmp = (' '.join(output.split())).split(" ")
    tmp_dict['total_hdd'] = float(values_tmp[1].replace("G",""))
    tmp_dict['used_hdd'] = float(values_tmp[2].replace("G",""))
    free_hd_per = round(((tmp_dict['total_hdd'] - tmp_dict['used_hdd']) / (tmp_dict['total_hdd'])) * 100, 2)
    tmp_dict['free_hdd_per'] = free_hd_per
    return tmp_dict


def direct_stats(output) :
    out_tmp = output.split("\n")
    cpu = float(out_tmp[2].split(",")[0].split(": ")[1].replace('%us',"").replace("us",""))
    mem_tmp = out_tmp[3].split(",")
    total_mem = round(float(
        mem_tmp[0].split(":")[1].lstrip().replace("k", "").replace(" total", "").replace("+total","").rstrip()) / float(
        1024 * 1024), 2)

    for item in mem_tmp[1:]:
        if 'free' in item:
            free_mem = round(
                float(item.lstrip().replace("k", "").replace(" free", "").replace("+free", "").rstrip()) / float(
                    1024 * 1024), 2)
        elif 'used' in item:
            ix = item.find('used')
            item1 = item[:ix]
            used_mem = round(
                float(item1.lstrip().replace("k", "").replace(" used", "").replace("+used", "").rstrip()) / float(
                    1024 * 1024), 2)

    swap_tmp = out_tmp[4].split(",")
    total_swap = round(float(
        swap_tmp[0].split(":")[1].lstrip().replace("k", "").replace(" total", "").replace("+total","").rstrip()) / float(
        1024 * 1024), 2)
    for item in swap_tmp[1:]:
        if 'free' in item:
            free_swap = round(
                float(item.lstrip().replace("k", "").replace(" free", "").replace("+free", "").rstrip()) / float(
                    1024 * 1024), 2)
        elif 'used' in item:
            ix = item.find('used')
            item1 = item[:ix]
            used_swap = round(
                float(item1.lstrip().replace("k", "").replace(" used", "").replace("+used", "").rstrip()) / float(
                    1024 * 1024), 2)

    free_mem_per = round((free_mem / total_mem) * 100, 2)
    used_mem_per = round((used_mem / total_mem) * 100, 2)

    if total_swap != 0 :
        free_swap_per = round((free_swap / total_swap) * 100, 2)
        used_swap_per = round((used_swap / total_swap) * 100, 2)
    else :
        free_swap = 0
        used_swap = 0
        free_swap_per = 0
        used_swap_per = 0

    final_dict = {'cpu_info': cpu, 'total_mem': total_mem,'free_mem': free_mem,'free_mem_per' : free_mem_per, 'used_mem': used_mem, 'used_mem_per' : used_mem_per, 'total_swap': total_swap, 'free_swap': free_swap,
                  'free_swap_per' : free_swap_per, 'used_swap': used_swap, 'used_swap_per' : used_swap_per, 'Source' : 'Direct computation'}
    return final_dict


def sar_stats(out_cpu, out_mem, out_swap):
    stats_dict = {}
    out_cpu_tmp = out_cpu.split("\n")
    max_cpu_utilisation = 0.0
    for val in out_cpu_tmp:
        if 'linux' in val.lower() or 'cpu' in val.lower() or 'average' in val.lower():
            continue
        elif not val:
            continue
        else:
            values_tmp = (' '.join(val.split())).split(" ")
            if max_cpu_utilisation < float(values_tmp[3]):
                max_cpu_utilisation = float(values_tmp[3])

    total_mem = 0
    free_mem_max = 0
    used_mem_max = 0
    out_mem_tmp = out_mem.split("\n")

    for val in out_mem_tmp:
        if 'linux' in val.lower() or 'kbmemfree' in val.lower() or 'average' in val.lower():
            continue
        elif not val:
            continue
        else:
            values_tmp = (' '.join(val.split())).split(" ")
            total_mem = float(values_tmp[2]) + float(values_tmp[3])
            if free_mem_max < float(values_tmp[2]):
                free_mem_max = float(values_tmp[2])
            if used_mem_max < float(values_tmp[3]):
                used_mem_max = float(values_tmp[3])

    total_swap = 0
    free_swap_max = 0
    used_swap_max = 0
    out_swap_tmp = out_swap.split("\n")

    for val in out_swap_tmp:
        if 'linux' in val.lower() or 'kbswpfree' in val.lower() or 'average' in val.lower():
            continue
        elif not val:
            continue
        else:
            values_tmp = (' '.join(val.split())).split(" ")
            total_swap = float(values_tmp[2]) + float(values_tmp[3])
            if free_swap_max < float(values_tmp[2]):
                free_swap_max = float(values_tmp[2])
            if used_swap_max < float(values_tmp[3]):
                used_swap_max = float(values_tmp[3])

    free_mem_max_per = round((free_mem_max / total_mem) * 100, 2)
    free_mem_max_new = round(free_mem_max / (1024 * 1024),2)
    used_mem_max_per = round((used_mem_max / total_mem) * 100, 2)
    used_mem_max_new = round(used_mem_max / (1024 * 1024),2)

    if total_swap != 0 :
        free_swap_max_per = round((free_swap_max / total_swap) * 100, 2)
        free_swap_max_new = round(free_swap_max / (1024 * 1024), 2)
        used_swap_max_per = round((used_swap_max / total_swap) * 100, 2)
        used_swap_max_new = round(used_swap_max / (1024 * 1024), 2)
    else :
        free_swap_max_per = 0
        free_swap_max_new = 0
        used_swap_max_per = 0
        used_swap_max_new = 0

    final_dict = {'cpu_info': max_cpu_utilisation , 'total_mem': round(total_mem / (1024 * 1024),2), 'free_mem': free_mem_max_new, 'free_mem_per' : free_mem_max_per, 'used_mem': used_mem_max_new,'used_mem_per' : used_mem_max_per, 'total_swap': round(total_swap / (1024 * 1024),2), 'free_swap': free_swap_max_new,
                  'free_swap_per' : free_swap_max_per, 'used_swap': used_swap_max_new,'used_swap_per' : used_swap_max_per, 'Source': 'Sar Logs'}
    return final_dict


def colored_row(color, sam_dict) :
    tmp_str = ""
    if color is 'blue':
        tmp_str = '''<tr style="background-color:#A3E4D7;">
           <td style="border:2px solid #0d0d0d;text-align:center;">{0}</td>
           <td style="border:2px solid #0d0d0d;text-align:center;">{1}</td>
           <td style="border:2px solid #0d0d0d;text-align:center;">{2}</td>
           <td style="border:2px solid #0d0d0d;text-align:center;">{3}</td>
           <td style="border:2px solid #0d0d0d;text-align:center;">{4}</td>
           </tr>'''.format(sam_dict['ip_address'],sam_dict['cpu_info'],sam_dict['used_mem_per'],sam_dict['used_swap_per'],sam_dict['free_hdd_per'])
    elif color is 'orange':
        tmp_str = '''<tr style="background-color:#FF7F50;">
           <td style="border:2px solid #0d0d0d;text-align:center;">{0}</td>
           <td style="border:2px solid #0d0d0d;text-align:center;">{1}</td>
           <td style="border:2px solid #0d0d0d;text-align:center;">{2}</td>
           <td style="border:2px solid #0d0d0d;text-align:center;">{3}</td>
           <td style="border:2px solid #0d0d0d;text-align:center;">{4}</td>
           </tr>'''.format(sam_dict['ip_address'],sam_dict['cpu_info'],sam_dict['used_mem_per'],sam_dict['used_swap_per'],sam_dict['free_hdd_per'])
    return tmp_str


def createHtml(complete_dict) :
    start_str = '''<!DOCTYPE html>
    <html lang="en">
    <head>
    	<meta charset="utf-8">
    	<title>Bootstrap For Beginners</title>
    	<meta name="description" content="Hello World">

    	<!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap-theme.min.css">
    <style>
    table {
        border-collapse: collapse;
    }
    </style>
    </head>
    <body>'''

    end_str = '''</tbody>
    </table>
    <br/><br/>
    </body>
    </html>'''

    table_str = '''<table class = "table" style="width:95%;border:2px solid #0d0d0d;text-align:center;">
       <caption style="text-align:center;margin-top:12px;background-color:#E3E5E4;color:#0d0d0d;font-size:16px;">
       <b>{0}</b>
       </caption>
       <thead>
          <tr style="background-color:#0d0d0d;color:#ffffff;">
             <th style="border:2px solid #0d0d0d;text-align:center;">IP</th>
    		 <th style="border:2px solid #0d0d0d;text-align:center;">CPU %</th>
             <th style="border:2px solid #0d0d0d;text-align:center;">USED MEM %</th>
             <th style="border:2px solid #0d0d0d;text-align:center;">USED SWAP %</th>
             <th style="border:2px solid #0d0d0d;text-align:center;">FREE HDD %</th>
          </tr>
       </thead>
       <tbody>'''

    final_str = start_str
    for key in complete_dict.keys():
        print complete_dict
        if len(complete_dict['successful_connections']) > 0:
            newlist = sorted(complete_dict['successful_connections'], key=lambda k: k['cpu_info'])
            newlist_final = sorted(newlist, key=lambda k: k['used_mem_per'])
            table_str_new = table_str.format(key)
            row_str = ""
            for values in newlist_final:
                if values['used_mem_per'] > 80 or values['cpu_info']>90 or values['free_hdd_per']<10 :
                    tmp_str = colored_row("orange", values)
                else:
                    tmp_str = colored_row("blue", values)

                row_str += tmp_str
            final_str += table_str_new + row_str + end_str

    send_mail_attachment(final_str)


def computeInfraPerf(allBoxes) :
    username_box = 'username'
    password_box = 'password'
    key = paramiko.RSAKey.from_private_key_file("/path/.ssh/id_rsa")
    command_direct = 'top -bn 1'
    command_total_disk = 'df -h --total | grep total'
    check_day = str((datetime.datetime.today().day -1)).zfill(2) 
    sar_file_name = 'sa' + str(check_day)
    filename = "/var/log/sa/" + sar_file_name
    command_check_sar = '[ -e {0} ]  && echo "true" || echo "false"'.format(filename)
    #command_check_sar = '[ -e {0} ]  && echo "true" || echo "false"'.format(filename)
    info_dict = {}
    info_dict['successful_connections'] = []
    #info_dict['failed_connections'] = []

    for machine_ip in allBoxes:
                hd_info = []
                final_dict1 = {}
                complete_dict = {}
                try:
               		client = paramiko.SSHClient()
                	proxy_command = paramiko.ProxyCommand('ssh -o VisualHostKey=no -W {}:22 username@{}'.format(
               		 machine_ip , 'bastion'))
                	client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
                	client.connect(machine_ip, username=username_box, pkey = key, sock=proxy_command)
                	stdin, stdout, stderr = client.exec_command(command_check_sar)
                	output = stdout.read()
                        print output
                	if 'true' in output:
                                print 'In true'
                        	command_cpu = 'sar -u -f {0}'.format(filename)
                        	command_mem = 'sar -r -f {0}'.format(filename)
                        	command_swap = 'sar -S -f {0}'.format(filename)
                        	stdin, stdout, stderr = client.exec_command(command_cpu)
                        	out_cpu = stdout.read()
                        	stdin, stdout, stderr = client.exec_command(command_mem)
                        	out_mem = stdout.read()
                        	stdin, stdout, stderr = client.exec_command(command_swap)
                        	out_swap = stdout.read()
                        	final_dict = sar_stats(out_cpu, out_mem, out_swap)
                                #final_dict['ip_address'] = machine_ip
                                #info_dict['successful_connections'].append(final_dict)
                                #stdin, stdout, stderr = client.exec_command(command_total_disk)
                                #output = stdout.read()
                                #hdd_dict = total_disk_size(output)
                                #free_hdd_per = hdd_dict['free_hdd_per']
                                #total_hd_size = hdd_dict['total_hdd']
                                #used_hdd = hdd_dict['used_hdd']
                                #final_dict['total_hd_size'] = total_hd_size
                                #final_dict['used_hd_size'] = used_hdd
                                #final_dict['result'] = 'success'
                                #final_dict['ip_address'] = machine_ip
                                #final_dict['free_hdd_per'] = free_hdd_per
 
                	else:
                                print 'In else'
                	        stdin, stdout, stderr = client.exec_command(command_direct)
                        	output = stdout.read()
                        	final_dict = direct_stats(output)

                      	stdin, stdout, stderr = client.exec_command(command_total_disk)
                       	output = stdout.read()
                       	hdd_dict = total_disk_size(output)
                       	free_hdd_per = hdd_dict['free_hdd_per']
                       	total_hd_size = hdd_dict['total_hdd']
                       	used_hdd = hdd_dict['used_hdd']
                       	final_dict['total_hd_size'] = total_hd_size
                       	final_dict['used_hd_size'] = used_hdd
                       	final_dict['result'] = 'success'
                       	final_dict['ip_address'] = machine_ip
                       	final_dict['free_hdd_per'] = free_hdd_per
                       	final_dict1['ip_address'] = machine_ip
                       	final_dict1['cpu_info'] = final_dict['cpu_info']
                       	final_dict1['used_mem_per'] = final_dict['used_mem_per']
                       	final_dict1['used_swap_per'] = final_dict['used_swap_per']
                       	final_dict1['free_hdd_per'] = free_hdd_per
                        info_dict['successful_connections'].append(final_dict1)
                        print 'info_dict'
                        print info_dict
                except Exception as e:
                       pass
                finally:
                    client.close()
                    #complete_dict[machine_ip] = info_dict
    print info_dict
    createHtml(info_dict)

def mother():
    allBoxes = ['IP1','IP2']
    password = 'password'
    username = 'username'
    computeInfraPerf(allBoxes)

if __name__ == "__main__":
    mother()

