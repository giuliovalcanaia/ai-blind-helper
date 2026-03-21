# Raspberry Pi OS - Installation Guide
[Click here to return to the README](README.md#installing-ai-blind-helper)

1. Go to https://www.raspberrypi.com/software/ and download the latest version of Raspberry Pi Imager for your operating system.
   1. If using Linux and you download the AppImage, make sure the file is marked as executable.
   2. Ubuntu installation: `sudo apt install rpi-imager`
   3. Arch Linux installation: `sudo pacman -S rpi-imager`
   4. Run the program with root privileges to ensure it can access and write to the SD card: `sudo rpi-imager`
   5. In some cases, such as when using Hyprland or Wayland, a special execution method is required to preserve environment variables: `sudo -E rpi-imager`
2. Insert the SD card into your computer.
3. Launch the Raspberry Pi Imager.
4. Select the **Raspberry Pi Zero 2 W** board and click Next ![](assets/select_device.png)
5. Choose **Raspberry Pi OS (Other)** ![](assets/select_other_os.png)
6. Select **Raspberry Pi OS Lite (64-bit)** and click Next ![](assets/select_pi_os_lite.png)
7. Choose your SD card and click Next. Ensure you select the correct device. Choosing the wrong option, such as an internal drive, may result in the loss of all your data! ![](assets/select_storage.png)
8. Enter the hostname: `ai-blind-helper` and click Next ![](assets/config_hostname.png)
9. Configure the localization settings according to your region.
10. Set a username and password.
11. Configure the Wi-Fi connection by entering your SSID and password.
12. **Very important!** Enable SSH via password authentication. This feature will be required later. ![](assets/config_ssh.png)
13. Raspberry Pi Connect is optional. For this guide, it will not be enabled.
14. Finally, review your configuration and click **WRITE** ![](assets/config_review.png)
15. The application will ask for confirmation. Choose **I UNDERSTAND, ERASE AND WRITE** (or **YES**) ![](assets/config_confirmation.png)
16. After this, the download and installation process will start automatically.
17. Once finished, you will see the following confirmation screen ![](assets/config_finish.png)
18. You can now safely remove the SD card.


[Click here to return to the README](README.md#installing-ai-blind-helper)