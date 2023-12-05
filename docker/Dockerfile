FROM debian:10-slim
RUN apt update && apt install openssh-server sudo -y
# Create a user “sshuser” and group “sshgroup”
RUN groupadd sshgroup && useradd -ms /bin/bash -g sshgroup debian
RUN adduser debian sudo

RUN echo 'debian:password' | chpasswd
RUN echo 'root:root' | chpasswd

RUN echo "debian ALL=(ALL:ALL) NOPASSWD: ALL"  | sudo tee /etc/sudoers.d/debian

# Create sshuser directory in home
RUN mkdir -p /home/debian/.ssh

RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

# Copy the ssh public key in the authorized_keys file. The idkey.pub below is a public key file you get from ssh-keygen. They are under ~/.ssh directory by default.
#COPY id_ed25519.pub /home/debian/.ssh/authorized_keys

# change ownership of the key file.
#RUN chown debian:sshgroup /home/debian/.ssh/authorized_keys && chmod 600 /home/debian/.ssh/authorized_keys

RUN mkdir /var/www/
RUN mkdir /var/www/public

# ask corrector the good way how we doing it
RUN chmod a+rwx /var/www/
RUN chmod a+rwx /var/www/public

# Start SSH service
RUN service ssh start

# Expose docker port 22
EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]
