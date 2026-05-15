import os
from tensorflow.keras.applications import Xception
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import Adam

DATA_DIR = 'data/'  # expects data/real/ and data/fake/
IMG_SIZE = (224,224)
BATCH_SIZE = 16
EPOCHS = 3  # set small for demo

def build_model():
    base = Xception(weights='imagenet', include_top=False, input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
    x = GlobalAveragePooling2D()(base.output)
    x = Dense(1024, activation='relu')(x)
    out = Dense(1, activation='sigmoid')(x)
    model = Model(inputs=base.input, outputs=out)
    for layer in base.layers:
        layer.trainable = False
    model.compile(optimizer=Adam(1e-4), loss='binary_crossentropy', metrics=['accuracy'])
    return model

if __name__ == '__main__':
    os.makedirs('model', exist_ok=True)
    train_datagen = ImageDataGenerator(rescale=1./255, horizontal_flip=True, validation_split=0.2)
    train_gen = train_datagen.flow_from_directory(DATA_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode='binary', subset='training')
    val_gen = train_datagen.flow_from_directory(DATA_DIR, target_size=IMG_SIZE, batch_size=BATCH_SIZE, class_mode='binary', subset='validation')

    model = build_model()
    model.fit(train_gen, validation_data=val_gen, epochs=EPOCHS)
    model.save('model/model.pth')
    print('Model saved to model/deepfake_model.h5')
