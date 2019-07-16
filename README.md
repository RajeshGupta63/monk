Problem statement

"Infra optimizer is a sysstat based important performance kpi (i.e memory,cpu,disk)monitoring suite, based on the stats collected user will make the decision weather vm running on prod needs to be scaled down or up. Below are some of the use cases : 1. Infra optimization 2. Monitoring servers after production deployments for any unusual performance activity 3. User will only get reports only for the servers in which he/she is interested"


Use cases

1. Infra(vm's) used will be of optimal size will lead to cost saving in cases where we have bigger aws machine deployed then required.
2. Down time due to memory, cpu crunch will be minimized. Based on the reports we can easily identify instances which needs to be scaled up/down.


How to use

Enable sysstat on the server

Step 1.  Install sysstat
sudo apt-get install sysstat

Step 2. Enable stat collection
sudo vi /etc/default/sysstat
change ENABLED=”false” to ENABLED=”true”
save the file

Step 3. Change the collection interval from every 10 minutes to every 2 minutes.
sudo vi /etc/cron.d/sysstat
Change
5-55/10 * * * * root command -v debian-sa1 > /dev/null && debian-sa1 1 1
To
*/2 * * * * root command -v debian-sa1 > /dev/null && debian-sa1 1 1
save the file

Step 4. Restart sysstat
sudo service sysstat restart


Open monk_infra_optimizer.py using below command

vi monk_infra_optimizer.py

Update list of servers to be analysed  in section as command(,) seperated list

allBoxes = ['IP1','IP2']

Save the file

Run using below command

python monk_infra_optimizer.py
