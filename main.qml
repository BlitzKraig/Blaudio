import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    visible: true
    width: 600
    height: 400
    title: "Slider Application"

    ListView {
        id: listView
        width: parent.width
        height: parent.height - button.height
        orientation: ListView.Horizontal
        model: sliderManager.sliders.length
        delegate: Item {
            width: 100
            height: listView.height

            Slider {
                id: slider
                orientation: Qt.Vertical
                width: parent.width
                height: parent.height - removeButton.height
            }

            Button {
                id: removeButton
                text: "X"
                width: parent.width
                anchors.top: slider.bottom
                onClicked: sliderManager.removeSlider(index)
            }
        }
    }

    Button {
        id: button
        text: "Add Slider"
        width: parent.width
        anchors.top: listView.bottom
        onClicked: sliderManager.addSlider()
    }
}