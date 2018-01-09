"""
Copyright 2017-2018 Fizyr (https://fizyr.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import print_function

from keras_retinanet.utils.image import preprocess_image, resize_image

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

import numpy as np
import json
import os


def evaluate_jh(generator, model, threshold=0.05):
    # start collecting results
    results = []
    image_ids = []
    #coco_true = coco.loadRes(coco.loadNumpyAnnotations(coco.createAnnNumpy('/data/users/xiziwang/tools/nsp/JHdevkit/VOC2007','val')))
    sexy2sexy = 0
    sexy2normal = 0
    sexy2erotic = 0
    erotic2sexy = 0
    erotic2erotic = 0
    erotic2normal = 0
    normal2erotic = 0
    normal2sexy = 0
    normal2normal = 0
    for i in range(generator.size()):
        image = generator.load_image(i)
        image = preprocess_image(image)
        image, scale = generator.resize_image(image)

        # run network
        _, _, detections,scores = model.predict_on_batch(np.expand_dims(image, axis=0))

        jhclasses = scores[0]
        pred = np.argmax(jhclasses) 
        filename = generator.load_image_name(i) 
        if pred == 0:
            if '/erotic/' in filename:
                erotic2normal += 1
            elif '/sexy/' in filename:
                sexy2normal += 1
            elif '/normal/' in filename:
                normal2normal += 1
        elif pred == 1:
            if '/erotic/' in filename:
                erotic2sexy += 1
            elif '/sexy/' in filename:
                sexy2sexy += 1
            elif '/normal/' in filename:
                normal2sexy += 1

        elif pred == 2:
            if '/erotic/' in filename:
                erotic2erotic += 1
            elif '/sexy/' in filename:
                sexy2erotic += 1
            elif '/normal/' in filename:
                normal2erotic += 1
        # clip to image shape
        detections[:, :, 0] = np.maximum(0, detections[:, :, 0])
        detections[:, :, 1] = np.maximum(0, detections[:, :, 1])
        detections[:, :, 2] = np.minimum(image.shape[1], detections[:, :, 2])
        detections[:, :, 3] = np.minimum(image.shape[0], detections[:, :, 3])

        # correct boxes for image scale
        detections[0, :, :4] /= scale

        # change to (x, y, w, h) (MS COCO standard)
        detections[:, :, 2] -= detections[:, :, 0]
        detections[:, :, 3] -= detections[:, :, 1]

        # compute predicted labels and scores
        for detection in detections[0, ...]:
            positive_labels = np.where(detection[4:] > threshold)[0]

            # append detections for each positively labeled class
            for label in positive_labels:
                image_result = {
                    #'image_id'    : generator.image_names[i],
                    'image_id' : i,
                    #'category_id' : generator.label_to_name(label),
                    'category_id' : label,
                    'score'       : float(detection[4 + label]),
                    'bbox'        : (detection[:4]).tolist(),
                }

                # append detection to results
                results.append(image_result)

        # append image to list of processed images
        image_ids.append(generator.image_names[i])

        # print progress
        print('{}/{}'.format(i, len(generator.image_names)), end='\r')

    #if not len(results):
        # return

    # write output

    print('erotic2erotic:{},erotic2sexy:{},erotic2normal:{},sexy2erotic:{},sexy2sexy:{},sexy2normal:{},normal2erotic:{},normal2sexy:{},normal2normal:{}'.format(erotic2erotic, erotic2sexy, erotic2normal, sexy2erotic, sexy2sexy, sexy2normal, normal2erotic, normal2sexy, normal2normal))

    '''
    json.dump(results, open('{}_bbox_results.json'.format(generator.set_name), 'w'), indent=4)
    json.dump(image_ids, open('{}_processed_image_ids.json'.format(generator.set_name), 'w'), indent=4)

    # load results in COCO evaluation tool
    #coco_true = generator.coco
    data_dir = '/data/users/xiziwang/tools/nsp/JHdevkit/VOC2007'
    coco = COCO()
    coco_true = coco.loadRes(coco.loadNumpyAnnotations(coco.createAnnNumpy('/data/users/xiziwang/tools/nsp/JHdevkit/VOC2007','test'))) 
    coco_pred = coco.loadRes('{}_bbox_results.json'.format(generator.set_name))

    # run COCO evaluation
    coco_eval = COCOeval(coco_true, coco_pred, 'bbox')
    # coco_eval.params.imgIds = image_ids
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()
    '''
