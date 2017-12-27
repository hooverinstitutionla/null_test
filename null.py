'''
This Python 3 script performs a null test between similarly named WAV files
in different directories. Following, it produces a report if the two files
are the same audio.
'''

import datetime
import logging
import os
import platform
import re
import subprocess
import sys
import wave


def run_command(command, operation):
    output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    message = output.stdout.read()
    output.kill()

    logging.info(operation)
    logging.info("\r\nCommand " + str(command) + "\r\n")
    if len(message) > 1:
        logging.info(message+"\r\n")
    return message

def get_loud(f, path):
    command = ['ffmpeg','-i', os.path.join(path, f), '-af', 'volumedetect', '-f', 'null', 'NUL']
    operation = 'Getting the maximum volume of %s now.' % f
    yo = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)

    logging.info(operation)
    logging.info("\r\nCommand " + str(command) + "\r\n")

    for line in yo.stdout:
        if 'max_volume' in line:
            line = line.rstrip()
            volume = line[line.find(':')+2:]

    volume = volume.rstrip()
    logging.info('The maximum volume of %s is: %s' % (f, volume))
    return volume

def check_channels(f, hi_res_path):
    full_file = os.path.join(hi_res_path, f)
    wav = wave.open(full_file, 'rb')
    channels = wav.getnchannels()
    wav.close()
    logging.info('%s has %s channels.', full_file, channels)
    return channels

def sixteen_bit(path, f):
    sixteen = f.split('.')[0]+"_16bit.wav"
    command = ['ffmpeg','-i',os.path.join(path, f), '-dither_method','modified_e_weighted', os.path.join(path, sixteen)]
    operation = 'Making the 16-bit version of %s now.' % f
    output = run_command(command, operation)
    return sixteen

def null_test(path1, path2, f):
    does_null = False
    channels = check_channels(f, path1)
    print("Working on %s now." % f)

    # Create 16-bit WAV files
    sixteen_a = sixteen_bit(path1, f)
    sixteen_b = sixteen_bit(path2, f)

    # Invert file in path2
    inverted = sixteen_b.split('.')[0]+"_i.wav"
    if channels == 1:
        inv_command = ['ffmpeg','-i', os.path.join(path2, sixteen_b), '-af', 'aeval=-val(0)', os.path.join(path2, inverted)]
    else:
        inv_command = ['ffmpeg','-i', os.path.join(path2, sixteen_b), '-af', 'aeval=-val(0)|-val(1)', os.path.join(path2, inverted)]
    operation = 'Making the inverted version of %s now.' % f
    output = run_command(inv_command, operation)

    # Mix files together
    mixed = f.split('.')[0]+"-mix.wav"
    mix_command = ['ffmpeg','-i',os.path.join(path1, sixteen_a),'-i', os.path.join(path2, inverted),'-filter_complex','amix', os.path.join(path2, mixed)]

    operation = 'Making the mixed version of %s now.' % f
    output = run_command(mix_command, operation)

    # toggle does_null based on volume of mixed file.
    peak = get_loud(mixed, path2)
    if peak == '-91.0 dB' or peak == '.0 dB':
        does_null = True

    # Remove the inverted and mixed files
    os.remove(os.path.join(path1, sixteen_a))
    os.remove(os.path.join(path2, sixteen_b))
    os.remove(os.path.join(path2, inverted))
    os.remove(os.path.join(path2, mixed))

    return does_null

def make_file_list(path1, path2):
    d1 = os.listdir(path1)
    file_list = []
    not_in_both = []

    for f in d1:
        if not os.path.isfile(os.path.join(path1, f)):
            continue

        file_name = f.split('.')
        if file_name[1] != 'wav':
            continue

        f2 = os.path.join(path2, f)
        if os.path.exists(f2):
            file_list.append(f)
        else:
            not_in_both.append(f)

    return file_list, not_in_both

def validate_path(path):
    # Guard against just the directory
    if re.match(r'^\w:$', path):
        path = path + '\\'

    re_result = re.match(r'^(\w:\\$)|(\w:\\).*\\$|^(/.*/)$', path)
    os_result = os.path.exists(path)
    permissions = os.access(path, os.W_OK)

    if re_result and os_result and permissions:
        result = True
    else:
        result = False

    return result

def get_paths():
    toggle = False
    while toggle is False:
        path1 = input("Where is the master directory? (Please include a trailing slash or backslash)\n")
        path2 = input("Where is the second directory? (Please include a trailing slash or backslash)\n")
        a = validate_path(path1)
        b = validate_path(path2)
        if a and b:
            toggle=True
            print()
        else:
            print('\r\nAt least one of those paths was invalid. Please try again.\r\n\r\n')

    return path1, path2

def main():
    path1, path2 = get_paths()
    file_list, not_in_both = make_file_list(path1, path2)

    try:
        filename = os.path.join(path1, str(datetime.date.today())+'_null_test.log')
        logging.basicConfig(filename=filename, level=logging.DEBUG)
    except:
        sys.exit('There\'s a permissions problem. Please try this program again. Plase make sure you can write to the folders in question.')

    same = []
    different = []

    # Compare the files.
    for f in file_list:
        does_null = null_test(path1, path2, f)
        if does_null:
            same.append(f)
        else:
            different.append(f)

    # Write the results of the tests
    results_file = os.path.join(path1, str(datetime.date.today())+'_results.txt')
    with open(results_file, 'w') as results:

        # Write what did null
        if len(same) < 1:
            results.write("\r\nNo files were found to be the same.\r\n")
        else:
            results.write("These files are the same:\r\n")
            for f in same:
                results.write(f+"\r\n")

        # Write what did not null
        if len(different) < 1:
            results.write("\r\nNo files were found to be different.\r\n")
        else:
            results.write("\r\nThese files are different:\r\n")
            for f in different:
                results.write(f+"\r\n")

        # Write into results what files were ignored
        if len(not_in_both) > 0:
            results.write("\r\nThe following files were ignored because they were not in the second directory.\r\n")
            for f in not_in_both:
                results.write(f+"\r\n")


    # Assistance with the following six lines of code was from StackOverlow
    # user Cas - http://stackoverflow.com/users/175584/cas
    # http://stackoverflow.com/questions/6631299/python-opening-a-folder-in-explorer-nautilus-mac-thingie
    # Creative Commons license outlined at http://blog.stackoverflow.com/2009/06/attribution-required/
    if platform.system() == "Windows":
        os.startfile(results_file)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", results_file])
    else:
        subprocess.Popen(["xdg-open", results_file])


if __name__ == '__main__':
    main()
