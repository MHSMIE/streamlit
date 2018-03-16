from keras.datasets import mnist
from keras.layers import Conv2D, MaxPooling2D, Dropout, Dense, Flatten
from keras.models import Sequential
from keras.optimizers import SGD
from keras.utils import np_utils
import keras
import math
import numpy as np
import pandas as pd
import sys

from streamlet import Notebook, Chart

class MyCallback(keras.callbacks.Callback):
    def __init__(self, x_test, print):
        self._x_test = x_test
        self._print = print

    def on_train_begin(self, logs=None):
        self._print.header('Summary', level=2)
        self._summary_chart = self._create_chart('area', 300)
        self._summary_stats = self._print.text(f'{"epoch":>8s} :  0')
        self._print.header('Training Log', level=2)

    def on_epoch_begin(self, epoch, logs=None):
        self._epoch = epoch
        self._print.header(f'Epoch {epoch}', level=3)
        self._epoch_chart = self._create_chart('line')
        self._epoch_progress = self._print.alert('No progress yet.')
        self._epoch_summary = self._print.alert('No stats yet.')

    def on_batch_end(self, batch, logs=None):
        rows = pd.DataFrame([[logs['loss'], logs['acc']]],
            columns=['loss', 'acc'])
        if batch % 10 == 0:
            self._epoch_chart.add_rows(rows)
        if batch % 100 == 99:
            self._summary_chart.add_rows(rows)
        percent_complete = logs['batch'] * logs['size'] /\
            self.params['samples']
        self._epoch_progress.progress(math.ceil(percent_complete * 100))
        self._epoch_summary(
            f"loss: {logs['loss']:>7.5f} | acc: {logs['acc']:>7.5f}")

    def on_epoch_end(self, epoch, logs=None):
        self._print.header('Summary', level=5)
        indices = np.random.choice(len(self._x_test), 36)
        test_data = self._x_test[indices]
        prediction = np.argmax(self.model.predict(test_data), axis=1)
        self._print.img(1.0 - test_data, caption=prediction)
        summary = '\n'.join(f'{k:>8s} : {v:>8.5f}' for (k, v) in logs.items())
        self._print(summary)
        self._summary_stats(f'{"epoch":>8s} :  {epoch}\n{summary}')

    def _create_chart(self, type='line', height=0):
        empty_data = pd.DataFrame(columns=['loss', 'acc'])
        epoch_chart = Chart(empty_data, f'{type}_chart', height=height)
        epoch_chart.y_axis(type='number',
            y_axis_id="loss_axis", allow_data_overflow="true")
        epoch_chart.y_axis(type='number', orientation='right',
            y_axis_id="acc_axis", allow_data_overflow="true")
        epoch_chart.cartesian_grid(stroke_dasharray='3 3')
        epoch_chart.legend()
        getattr(epoch_chart, type)(type='monotone', data_key='loss',
            stroke='rgb(44,125,246)', fill='rgb(44,125,246)',
            dot="false", y_axis_id='loss_axis')
        getattr(epoch_chart, type)(type='monotone', data_key='acc',
            stroke='#82ca9d', fill='#82ca9d',
            dot="false", y_axis_id='acc_axis')
        return self._print.chart(epoch_chart)

with Notebook() as print:
    print.header('MNIST CNN', level=1)

    (x_train, y_train), (x_test, y_test) = mnist.load_data()

    img_width=28
    img_height=28

    x_train = x_train.astype('float32')
    x_train /= 255.
    x_test = x_test.astype('float32')
    x_test /= 255.

    #reshape input data
    x_train = x_train.reshape(x_train.shape[0], img_width, img_height, 1)
    x_test = x_test.reshape(x_test.shape[0], img_width, img_height, 1)

    # one hot encode outputs
    y_train = np_utils.to_categorical(y_train)
    y_test = np_utils.to_categorical(y_test)
    num_classes = y_test.shape[1]

    sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)

    # build model

    model = Sequential()
    layer_1_size = 10
    epochs = 5

    model.add(Conv2D(10, (5, 5), input_shape=(img_width, img_height,1), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    #model.add(Conv2D(config.layer_2_size, (5, 5), input_shape=(img_width, img_height,1), activation='relu'))
    #model.add(MaxPooling2D(pool_size=(2, 2)))
    #model.add(Dropout(0.2))
    model.add(Flatten())
    model.add(Dense(8, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))

    model.compile(loss='categorical_crossentropy', optimizer=sgd,
        metrics=['accuracy'])
    model.fit(x_train, y_train, validation_data=(x_test, y_test),
        epochs=epochs, callbacks=[MyCallback(x_test, print)])

    print.alert('Finished training!', type='success')

    # model.save("convnet.h5")