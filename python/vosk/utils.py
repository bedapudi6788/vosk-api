import os
import shutil
import tarfile
import logging
import requests


MODEL_LINKS = {
    'en-us': 'https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-en-us-0.3.tar.gz',
    'cn': 'https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-cn-0.3.tar.gz',
    'de-zamia': 'https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-de-zamia-0.3.tar.gz',
    'es': 'https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-es-0.3.tar.gz',
    'fr-pguyot': 'https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-fr-pguyot-0.3.tar.gz',
    'pt': 'https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-pt-0.3.tar.gz',
    'ru': 'https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-ru-0.3.tar.gz',
    'spk-model': 'https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-spk-model-0.3.tar.gz'
}

VOSK_CORE_DIR = os.path.join(os.path.expanduser("~"), '.VOSK')

MB = 1024 * 1024

def download(model_name, save_to_path=None, timeout=10, redownload=False):
    if model_name not in MODEL_LINKS:
        logging.exception(str(model_name) + ' is not supported yet.')
        return False
    
    if not os.path.exists(VOSK_CORE_DIR):
        try:
            os.mkdir(VOSK_CORE_DIR)
        except Exception as ex:
            logging.exception(ex, exc_info=True)
            return False

    model_dir = os.path.join(VOSK_CORE_DIR, model_name)

    if os.path.exists(model_dir):
        if not redownload:
            return model_dir
        if redownload:
            shutil.rmtree(model_dir)

    model_url = MODEL_LINKS[model_name]

    tar_model_path = os.path.join(VOSK_CORE_DIR, os.path.basename(model_url))

    request = requests.get(model_url, timeout=timeout, stream=True, verify=True, allow_redirects=True)
    file_size = (float(request.headers['Content-length'])// MB) + 1

    success = True

    with open(tar_model_path, 'wb') as f:
        for chunk_i, chunk in enumerate(request.iter_content(MB)):
            try:
                chunk_i += 1
                completed_percent = str(int(100 * chunk_i/file_size)).zfill(3)
                print('Downloaded', completed_percent, '% of', file_size, 'MB' , end="\r")

                f.write(chunk)
            except Exception as ex:
                logging.exception('\n\n Download Failed \n\n')
                logging.exception(ex, exc_info=True)
                success = False
                break

    if not success:
        shutil.rmtree(tar_model_path)
        return False
    
    tar = tarfile.open(tar_model_path, "r:gz")
    tar_dir_path = os.path.join(VOSK_CORE_DIR, os.path.commonprefix(tar.getnames()))
    tar.extractall(VOSK_CORE_DIR)
    os.rename(tar_dir_path, model_dir)
    os.remove(tar_model_path)
    tar.close()

    return model_dir

if __name__ == '__main__':
    download('en-us')