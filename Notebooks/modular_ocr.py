from keras.datasets import mnist
from ocr_cnn import OCR_NeuralNetwork
from keras.models import Sequential
from keras.layers import Merge
import keras_image_utils as kiu
import numpy as np

class modular_ocr:

	def __init__(self, models=[]):
		self._models = []

		for model in models:
			self._models.append(model)


	def add_model(self, model):
		self._models.append(model)

	def compile_model(self, mode="ave", 
				      loss="categorical_crossentropy", 
					  optimizer="adadelta",
					  metrics=['accuracy', 'precision', 'recall']):

		if len(self._models) < 2:
			print("You need to at least to add 2 models to build an modular_ocr")
			return

		sequentials = []

		for model in self._models:
			sequentials.append(model._model)

		self._modular_ocr = Sequential()

		self._modular_ocr.add(Merge(sequentials, mode='ave'))

		self._modular_ocr.compile(loss='categorical_crossentropy',
		                     optimizer='adadelta',
		                     metrics=['accuracy', 'precision', 'recall'])

	# Fit all the models and compile it
	def fit(self, X_train, y_train, X_test=[], y_test=[], verbose=0):
		self._histories = []
		self._histories_cont = []

		for index, model in enumerate(self._models):
			print("Training model " + str(index) + " ...")

			window_size = 0;

			if index == 0:
				window_size = 30
			else:
				window_size = (-1)

			history, history_cont = model.fit(X_train, y_train, 
				X_test, y_test, forceRetrain = True, verbose=verbose, 
				initial_epoch=0, window_size=window_size, seed=1337)

			self._histories.append(history)
			self._histories_cont.append(history_cont)

		self.compile_model()

		print("Done.\n\n")

	def predict(self, X_test, verbose=0):

		if not self._modular_ocr:
			print("You must train the net first")
			return

		X_test, _ = kiu.adjust_input(X_test)
		return self._modular_ocr.predict([np.asarray(X_test)] * len(self._models))

	def evaluate(self, X_test, y_test, verbose=0):

		_, X_test, y_test = kiu.adjust_input_output(X_test, y_test, self._models[0]._nb_classes)

		print('Evaluating modular_ocr')

		score = self._modular_ocr.evaluate([np.asarray(X_test)] * len(self._models), 
			                             y_test, 
			                             verbose=verbose)

		print('Test accuracy:', score[1]*100, '%')
		print('Test error:', (1-score[2])*100, '%')



def main():
    ## Fast Usage
    
    # Prepare the dataset
    (X_train, y_train), (X_test, y_test) = mnist.load_data()

    # Initialization
    nn1 = OCR_NeuralNetwork(10, nb_epochs=2, model_dir="checkpoints", model_name="test1", batch_size=128)
    nn2 = OCR_NeuralNetwork(10, nb_epochs=2, model_dir="checkpoints", model_name="test2", batch_size=128)

    # You can add models in the constructor or by the add_model method
    # as follows
    models = [nn1,nn2]

    nn_modular_ocr = modular_ocr(models=models);

    nn3 = OCR_NeuralNetwork(10, nb_epochs=4, model_dir="checkpoints", model_name="test3", batch_size=128)

    nn_modular_ocr.add_model(nn3)

    # Training, not needed now because a snapshot of the model 
    # is present in the folder "checkpoints", if not uncomment this
    # line and refit the model
    nn_modular_ocr.fit(X_train, y_train, X_test, y_test, verbose=0)

    # Compile the model using the already fit nets. If you are
    # fitting from scracth, then uncomment the line above and
    # comment this line, since the compilation of the model
    # is done in the fit method of the modular_ocr
    #nn_modular_ocr.compile_model()

    # Prediciton
    predicted = nn_modular_ocr.predict(X_test)

    # Evaluation
    score = nn_modular_ocr.evaluate(X_test, y_test, verbose=1)


# Execute the module if it is main
if __name__ == "__main__":
    main()